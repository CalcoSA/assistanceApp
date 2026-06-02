from app.domain.entities.SpecificTrainingProgram import SpecificTrainingProgram
from app.domain.interfaces.IReportRepository import IReportRepository
from app.domain.entities.AttendancePerson import AttendancePerson
from app.domain.entities.SolutionCenter import SolutionCenter
from app.domain.entities.PersonnelType import PersonnelType
from app.domain.entities.EventCategory import EventCategory
from app.domain.entities.Attendance import Attendance
from sqlalchemy import func, distinct, case, and_
from app.domain.entities.Event import Event
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

class ReportRepository(IReportRepository):

    EXTERNAL_SOLUTION_CENTER_NAME = "personal externo"
    SST_SOLUTION_CENTER_NAME = "sst"
    CATEGORY_MULTIPLE_FUNCTIONS_NAME = "multiples funciones"
    CATEGORY_POSITION_NAME = "cargo"
    CATEGORY_PERSONAL_NAME = "personal"
    PROGRAM_SER_NAME = "ser"
    PROGRAM_HACER_NAME = "hacer"
    ADMINISTRATIVE_PERSONNEL_TYPE_NAME = "administrativo"
    QUALITY_SOLUTION_CENTER_NAME = "calidad"

    def __init__(self, db: Session):
        self.db = db

    def _applyDateFilters(self, query, dateFrom: Optional[date], dateTo: Optional[date]):
        if dateFrom:
            query = query.filter(Event.dateEvent >= dateFrom)

        if dateTo:
            query = query.filter(Event.dateEvent <= dateTo)

        return query

    def getTrainingSummary(self, dateFrom: Optional[date], dateTo: Optional[date],):
        query = (
            self.db.query(
                func.count(
                    distinct(AttendancePerson.IdAttendancePerson)
                ).label("totalTrainedPeople"),

                func.count(
                    distinct(
                        case(
                            (
                                func.lower(func.trim(SolutionCenter.nameSolutionCenter))
                                != self.EXTERNAL_SOLUTION_CENTER_NAME,
                                AttendancePerson.IdAttendancePerson
                            )
                        )
                    )
                ).label("totalInternalTrainedPeople"),

                func.count(
                    distinct(
                        case(
                            (
                                func.lower(func.trim(SolutionCenter.nameSolutionCenter))
                                == self.EXTERNAL_SOLUTION_CENTER_NAME,
                                AttendancePerson.IdAttendancePerson
                            )
                        )
                    )
                ).label("totalExternalTrainedPeople"),
            )
            .join(Attendance, Attendance.IdAttendancePerson == AttendancePerson.IdAttendancePerson)
            .join(Event, Event.IdEvent == Attendance.IdEvent)
            .outerjoin(SolutionCenter, SolutionCenter.IdSolutionCenter == AttendancePerson.IdSolutionCenter)
        )

        query = self._applyDateFilters(query, dateFrom, dateTo)
        result = query.first()

        return {
            "totalTrainedPeople": result.totalTrainedPeople or 0,
            "totalInternalTrainedPeople": result.totalInternalTrainedPeople or 0,
            "totalExternalTrainedPeople": result.totalExternalTrainedPeople or 0,
        }

    def getTrainingBySolutionCenter(self, dateFrom: Optional[date], dateTo: Optional[date],):
        query = (
            self.db.query(
                SolutionCenter.nameSolutionCenter.label("nameSolutionCenter"),
                func.count(
                    distinct(AttendancePerson.IdAttendancePerson)
                ).label("totalTrainedPeople"),
            )
            .join(Attendance, Attendance.IdAttendancePerson == AttendancePerson.IdAttendancePerson)
            .join(Event, Event.IdEvent == Attendance.IdEvent)
            .outerjoin(SolutionCenter, SolutionCenter.IdSolutionCenter == AttendancePerson.IdSolutionCenter)
        )

        query = self._applyDateFilters(query, dateFrom, dateTo)

        return (
            query
            .group_by(SolutionCenter.nameSolutionCenter)
            .order_by(SolutionCenter.nameSolutionCenter.asc())
            .all()
        )
    
    def _eventDurationHoursExpression(self):
        return (func.time_to_sec(func.timediff(Event.endTimeEvent, Event.startTimeEvent)) / 3600)

    def getSstTrainingSummary(self, dateFrom: Optional[date], dateTo: Optional[date],):
        eventSolutionCenter = SolutionCenter.__table__.alias("eventSolutionCenter")
        personSolutionCenter = SolutionCenter.__table__.alias("personSolutionCenter")

        internalPeopleQuery = (
            self.db.query(
                func.count(
                    distinct(AttendancePerson.IdAttendancePerson)
                ).label("totalInternalSstTrainedPeople")
            )
            .join(Attendance, Attendance.IdAttendancePerson == AttendancePerson.IdAttendancePerson)
            .join(Event, Event.IdEvent == Attendance.IdEvent)
            .outerjoin(
                eventSolutionCenter,
                eventSolutionCenter.c.IdSolutionCenter == Event.IdSolutionCenter
            )
            .outerjoin(
                personSolutionCenter,
                personSolutionCenter.c.IdSolutionCenter == AttendancePerson.IdSolutionCenter
            )
            .filter(
                func.lower(func.trim(eventSolutionCenter.c.nameSolutionCenter)) == self.SST_SOLUTION_CENTER_NAME
            )
            .filter(
                func.lower(func.trim(personSolutionCenter.c.nameSolutionCenter)) != self.EXTERNAL_SOLUTION_CENTER_NAME
            )
        )

        internalPeopleQuery = self._applyDateFilters(internalPeopleQuery, dateFrom, dateTo)

        totalInternalPeople = internalPeopleQuery.scalar() or 0

        hoursQuery = (
            self.db.query(
                func.coalesce(
                    func.sum(self._eventDurationHoursExpression()),
                    0
                ).label("totalSstTrainingHours")
            )
            .outerjoin(
                eventSolutionCenter,
                eventSolutionCenter.c.IdSolutionCenter == Event.IdSolutionCenter
            )
            .filter(
                func.lower(func.trim(eventSolutionCenter.c.nameSolutionCenter)) == self.SST_SOLUTION_CENTER_NAME
            )
        )

        hoursQuery = self._applyDateFilters(hoursQuery, dateFrom, dateTo)

        totalHours = hoursQuery.scalar() or 0

        return {
            "totalInternalSstTrainedPeople": int(totalInternalPeople),
            "totalSstTrainingHours": round(float(totalHours), 2),
        }

    def getSstTrainingByCollaborator(self, dateFrom: Optional[date], dateTo: Optional[date],):
        eventSolutionCenter = SolutionCenter.__table__.alias("eventSolutionCenter")
        personSolutionCenter = SolutionCenter.__table__.alias("personSolutionCenter")

        query = (
            self.db.query(
                AttendancePerson.documentNumberAttendancePerson.label("documentNumberAttendancePerson"),
                AttendancePerson.fullNameAttendancePerson.label("fullNameAttendancePerson"),
                personSolutionCenter.c.nameSolutionCenter.label("nameSolutionCenter"),
                func.coalesce(
                    func.sum(self._eventDurationHoursExpression()),
                    0
                ).label("totalSstTrainingHours"),
            )
            .join(Attendance, Attendance.IdAttendancePerson == AttendancePerson.IdAttendancePerson)
            .join(Event, Event.IdEvent == Attendance.IdEvent)
            .outerjoin(
                eventSolutionCenter,
                eventSolutionCenter.c.IdSolutionCenter == Event.IdSolutionCenter
            )
            .outerjoin(
                personSolutionCenter,
                personSolutionCenter.c.IdSolutionCenter == AttendancePerson.IdSolutionCenter
            )
            .filter(
                func.lower(func.trim(eventSolutionCenter.c.nameSolutionCenter)) == self.SST_SOLUTION_CENTER_NAME
            )
            .filter(
                func.lower(func.trim(personSolutionCenter.c.nameSolutionCenter)) != self.EXTERNAL_SOLUTION_CENTER_NAME
            )
        )

        query = self._applyDateFilters(query, dateFrom, dateTo)

        return (
            query
            .group_by(
                AttendancePerson.documentNumberAttendancePerson,
                AttendancePerson.fullNameAttendancePerson,
                personSolutionCenter.c.nameSolutionCenter,
            )
            .order_by(func.sum(self._eventDurationHoursExpression()).desc())
            .all()
        )
    
    def getTrainingHoursSummary(self, dateFrom: Optional[date], dateTo: Optional[date],):
        durationHours = self._eventDurationHoursExpression()
        personSolutionCenter = SolutionCenter.__table__.alias("personSolutionCenter")

        query = (
            self.db.query(
                func.coalesce(func.sum(durationHours), 0).label("totalTrainingHours"),

                func.coalesce(
                    func.sum(
                        case(
                            (
                                func.lower(func.trim(EventCategory.nameEventCategory))
                                == self.CATEGORY_MULTIPLE_FUNCTIONS_NAME,
                                durationHours,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("totalMultipleFunctionsTrainingHours"),

                func.coalesce(
                    func.sum(
                        case(
                            (
                                func.lower(func.trim(EventCategory.nameEventCategory))
                                == self.CATEGORY_POSITION_NAME,
                                durationHours,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("totalPositionTrainingHours"),

                func.coalesce(
                    func.sum(
                        case(
                            (
                                func.lower(func.trim(EventCategory.nameEventCategory))
                                == self.CATEGORY_PERSONAL_NAME,
                                durationHours,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("totalPersonalTrainingHours"),

                func.coalesce(
                    func.sum(
                        case(
                            (
                                func.lower(func.trim(SpecificTrainingProgram.nameSpecificTrainingProgram))
                                == self.PROGRAM_SER_NAME,
                                durationHours,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("totalSerTrainingHours"),

                func.coalesce(
                    func.sum(
                        case(
                            (
                                func.lower(func.trim(SpecificTrainingProgram.nameSpecificTrainingProgram))
                                == self.PROGRAM_HACER_NAME,
                                durationHours,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("totalHacerTrainingHours"),

                func.coalesce(
                    func.sum(
                        case(
                            (
                                func.coalesce(
                                    func.lower(func.trim(personSolutionCenter.c.nameSolutionCenter)),
                                    ""
                                ) != self.EXTERNAL_SOLUTION_CENTER_NAME,
                                durationHours,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("totalInternalTrainingHours"),

                func.coalesce(
                    func.sum(
                        case(
                            (
                                func.lower(func.trim(personSolutionCenter.c.nameSolutionCenter))
                                == self.EXTERNAL_SOLUTION_CENTER_NAME,
                                durationHours,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("totalExternalTrainingHours"),
            )
            .outerjoin(EventCategory, EventCategory.IdEventCategory == Event.IdEventCategory)
            .outerjoin(
                SpecificTrainingProgram,
                SpecificTrainingProgram.IdSpecificTrainingProgram == Event.IdSpecificTrainingProgram,
            )
            .outerjoin(Attendance, Attendance.IdEvent == Event.IdEvent)
            .outerjoin(AttendancePerson, AttendancePerson.IdAttendancePerson == Attendance.IdAttendancePerson)
            .outerjoin(
                personSolutionCenter,
                personSolutionCenter.c.IdSolutionCenter == AttendancePerson.IdSolutionCenter,
            )
        )

        query = self._applyDateFilters(query, dateFrom, dateTo)

        result = query.first()

        return {
            "totalTrainingHours": round(float(result.totalTrainingHours or 0), 2),
            "totalMultipleFunctionsTrainingHours": round(float(result.totalMultipleFunctionsTrainingHours or 0), 2),
            "totalPositionTrainingHours": round(float(result.totalPositionTrainingHours or 0), 2),
            "totalPersonalTrainingHours": round(float(result.totalPersonalTrainingHours or 0), 2),
            "totalSerTrainingHours": round(float(result.totalSerTrainingHours or 0), 2),
            "totalHacerTrainingHours": round(float(result.totalHacerTrainingHours or 0), 2),
            "totalInternalTrainingHours": round(float(result.totalInternalTrainingHours or 0), 2),
            "totalExternalTrainingHours": round(float(result.totalExternalTrainingHours or 0), 2),
        }
    
    def getNewStaffInductionSummary(self, dateFrom: Optional[date], dateTo: Optional[date],):
        durationHours = self._eventDurationHoursExpression()

        hoursQuery = (
            self.db.query(
                func.coalesce(
                    func.sum(durationHours),
                    0
                ).label("totalNewStaffInductionHours")
            )
            .filter(Event.isNewStaffInductionEvent == True)
        )

        hoursQuery = self._applyDateFilters(hoursQuery, dateFrom, dateTo)

        totalHours = hoursQuery.scalar() or 0

        peopleQuery = (
            self.db.query(
                func.count(
                    distinct(AttendancePerson.IdAttendancePerson)
                ).label("totalNewStaffInductionPeople")
            )
            .join(Attendance, Attendance.IdAttendancePerson == AttendancePerson.IdAttendancePerson)
            .join(Event, Event.IdEvent == Attendance.IdEvent)
            .filter(Event.isNewStaffInductionEvent == True)
        )

        peopleQuery = self._applyDateFilters(peopleQuery, dateFrom, dateTo)

        totalPeople = peopleQuery.scalar() or 0

        return {
            "totalNewStaffInductionHours": round(float(totalHours), 2),
            "totalNewStaffInductionPeople": int(totalPeople),
        }
    
    def getAdministrativeInductionSummary(self, dateFrom: Optional[date], dateTo: Optional[date],):
        durationHours = self._eventDurationHoursExpression()

        query = (
            self.db.query(
                func.coalesce(
                    func.sum(durationHours),
                    0
                ).label("totalAdministrativeInductionHours"),

                func.count(
                    distinct(AttendancePerson.IdAttendancePerson)
                ).label("totalAdministrativeInductionPeople"),
            )
            .join(Attendance, Attendance.IdEvent == Event.IdEvent)
            .join(
                AttendancePerson,
                AttendancePerson.IdAttendancePerson == Attendance.IdAttendancePerson,
            )
            .join(
                PersonnelType,
                PersonnelType.IdPersonnelType == Attendance.IdPersonnelType,
            )
            .filter(Event.isNewStaffInductionEvent == True)
            .filter(
                func.lower(func.trim(PersonnelType.namePersonnelType))
                == self.ADMINISTRATIVE_PERSONNEL_TYPE_NAME
            )
        )

        query = self._applyDateFilters(query, dateFrom, dateTo)

        result = query.first()

        return {
            "totalAdministrativeInductionHours": round(float(result.totalAdministrativeInductionHours or 0), 2),
            "totalAdministrativeInductionPeople": int(result.totalAdministrativeInductionPeople or 0),
        }
    
    def getGeneralSummary(self, dateFrom: Optional[date], dateTo: Optional[date],):
        eventSolutionCenter = SolutionCenter.__table__.alias("eventSolutionCenter")
        personSolutionCenter = SolutionCenter.__table__.alias("personSolutionCenter")

        internalFilter = (
            func.coalesce(
                func.lower(func.trim(personSolutionCenter.c.nameSolutionCenter)),
                ""
            ) != self.EXTERNAL_SOLUTION_CENTER_NAME
        )

        topCenterQuery = (
            self.db.query(
                eventSolutionCenter.c.nameSolutionCenter.label("nameSolutionCenter"),
                func.count(
                    distinct(AttendancePerson.IdAttendancePerson)
                ).label("totalTrainedPeople"),
            )
            .select_from(Event)
            .join(Attendance, Attendance.IdEvent == Event.IdEvent)
            .join(
                AttendancePerson,
                AttendancePerson.IdAttendancePerson == Attendance.IdAttendancePerson,
            )
            .outerjoin(
                eventSolutionCenter,
                eventSolutionCenter.c.IdSolutionCenter == Event.IdSolutionCenter,
            )
            .outerjoin(
                personSolutionCenter,
                personSolutionCenter.c.IdSolutionCenter == AttendancePerson.IdSolutionCenter,
            )
            .filter(internalFilter)
        )

        topCenterQuery = self._applyDateFilters(topCenterQuery, dateFrom, dateTo)

        topCenter = (
            topCenterQuery
            .group_by(eventSolutionCenter.c.nameSolutionCenter)
            .order_by(func.count(distinct(AttendancePerson.IdAttendancePerson)).desc())
            .first()
        )

        summaryQuery = (
            self.db.query(
                func.count(
                    distinct(
                        case(
                            (
                                func.lower(func.trim(eventSolutionCenter.c.nameSolutionCenter))
                                == self.QUALITY_SOLUTION_CENTER_NAME,
                                AttendancePerson.IdAttendancePerson,
                            )
                        )
                    )
                ).label("totalInternalQualityTrainedPeople"),

                func.count(
                    distinct(
                        case(
                            (
                                func.lower(func.trim(SpecificTrainingProgram.nameSpecificTrainingProgram))
                                == self.PROGRAM_SER_NAME,
                                AttendancePerson.IdAttendancePerson,
                            )
                        )
                    )
                ).label("totalInternalSerTrainedPeople"),

                func.count(
                    distinct(
                        case(
                            (
                                func.lower(func.trim(SpecificTrainingProgram.nameSpecificTrainingProgram))
                                == self.PROGRAM_HACER_NAME,
                                AttendancePerson.IdAttendancePerson,
                            )
                        )
                    )
                ).label("totalInternalHacerTrainedPeople"),
            )
            .select_from(Event)
            .join(Attendance, Attendance.IdEvent == Event.IdEvent)
            .join(
                AttendancePerson,
                AttendancePerson.IdAttendancePerson == Attendance.IdAttendancePerson,
            )
            .outerjoin(
                eventSolutionCenter,
                eventSolutionCenter.c.IdSolutionCenter == Event.IdSolutionCenter,
            )
            .outerjoin(
                personSolutionCenter,
                personSolutionCenter.c.IdSolutionCenter == AttendancePerson.IdSolutionCenter,
            )
            .outerjoin(
                SpecificTrainingProgram,
                SpecificTrainingProgram.IdSpecificTrainingProgram == Event.IdSpecificTrainingProgram,
            )
            .filter(internalFilter)
        )

        summaryQuery = self._applyDateFilters(summaryQuery, dateFrom, dateTo)

        summary = summaryQuery.first()

        return {
            "topTrainingSolutionCenterName": topCenter.nameSolutionCenter if topCenter else "SIN DATOS",
            "topTrainingSolutionCenterTotal": int(topCenter.totalTrainedPeople or 0) if topCenter else 0,
            "totalInternalQualityTrainedPeople": int(summary.totalInternalQualityTrainedPeople or 0),
            "totalInternalSerTrainedPeople": int(summary.totalInternalSerTrainedPeople or 0),
            "totalInternalHacerTrainedPeople": int(summary.totalInternalHacerTrainedPeople or 0),
        }
    
    def getAverageTrainingTimeSummary(self, dateFrom: Optional[date], dateTo: Optional[date], totalWorkers: int,):
        durationHours = self._eventDurationHoursExpression()
        personSolutionCenter = SolutionCenter.__table__.alias("personSolutionCenter")

        query = (
            self.db.query(
                func.coalesce(
                    func.sum(
                        case(
                            (
                                func.coalesce(
                                    func.lower(func.trim(personSolutionCenter.c.nameSolutionCenter)),
                                    ""
                                ) != self.EXTERNAL_SOLUTION_CENTER_NAME,
                                durationHours,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("totalInternalTrainingHours")
            )
            .select_from(Event)
            .join(Attendance, Attendance.IdEvent == Event.IdEvent)
            .join(
                AttendancePerson,
                AttendancePerson.IdAttendancePerson == Attendance.IdAttendancePerson,
            )
            .outerjoin(
                personSolutionCenter,
                personSolutionCenter.c.IdSolutionCenter == AttendancePerson.IdSolutionCenter,
            )
        )

        query = self._applyDateFilters(query, dateFrom, dateTo)

        totalInternalTrainingHours = float(query.scalar() or 0)

        averageTrainingHoursPerWorker = (
            totalInternalTrainingHours / totalWorkers
            if totalWorkers > 0
            else 0
        )

        return {
            "totalWorkers": totalWorkers,
            "totalInternalTrainingHours": round(totalInternalTrainingHours, 2),
            "averageTrainingHoursPerWorker": round(averageTrainingHoursPerWorker, 2),
        }