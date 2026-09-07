from app.domain.entities.SpecificTrainingProgram import SpecificTrainingProgram
from app.domain.interfaces.IReportRepository import IReportRepository
from app.domain.entities.AttendancePerson import AttendancePerson
from app.domain.entities.SolutionCenter import SolutionCenter
from app.domain.entities.PersonnelType import PersonnelType
from app.domain.entities.EventCategory import EventCategory
from app.domain.entities.EventTopic import EventTopic
from app.domain.entities.AssistanceReason import AssistanceReason
from app.domain.entities.EventCompetency import EventCompetency
from app.domain.entities.Competency import Competency
from app.domain.entities.Attendance import Attendance
from sqlalchemy import func, distinct, case, and_, or_
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
    INDUCTION_ASSISTANCE_REASON_NAME = "inducción"
    TRANSVERSAL_ASSISTANCE_REASON_NAME = "transversales"
    SERVICE_COMPETENCY_NAME = "actitud de servicio"
    THEMATIC_TRAINING_KEYS = {
        "INOCUIDAD",
        "SERVICIO",
        "PRODUCTO",
        "INDUCCION",
        "SER",
    }

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

    def getTrainingDetailsBySolutionCenter(self, dateFrom: Optional[date], dateTo: Optional[date],):
        personSolutionCenter = SolutionCenter.__table__.alias("personSolutionCenterDetail")

        query = (
            self.db.query(
                personSolutionCenter.c.nameSolutionCenter.label("nameSolutionCenter"),
                Event.IdEvent.label("IdEvent"),
                Event.titleEvent.label("titleEvent"),
                Event.dateEvent.label("dateEvent"),
                AttendancePerson.documentNumberAttendancePerson.label("documentNumberAttendancePerson"),
                AttendancePerson.fullNameAttendancePerson.label("fullNameAttendancePerson"),
                self._eventDurationHoursExpression().label("trainingHours"),
            )
            .select_from(Attendance)
            .join(Event, Event.IdEvent == Attendance.IdEvent)
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

        return query.order_by(
            personSolutionCenter.c.nameSolutionCenter.asc(),
            Event.dateEvent.desc(),
            Event.titleEvent.asc(),
            AttendancePerson.fullNameAttendancePerson.asc(),
        ).all()

    def getTrainingByCompetency(self, dateFrom: Optional[date], dateTo: Optional[date],):
        query = (
            self.db.query(
                Competency.nameCompetency.label("nameCompetency"),
                func.count(distinct(Event.IdEvent)).label("totalEvents"),
                func.count(distinct(Attendance.IdAttendance)).label("totalTrainedPeople"),
            )
            .select_from(EventCompetency)
            .join(Event, Event.IdEvent == EventCompetency.IdEvent)
            .join(Competency, Competency.IdCompetency == EventCompetency.IdCompetency)
            .outerjoin(Attendance, Attendance.IdEvent == Event.IdEvent)
        )

        query = self._applyDateFilters(query, dateFrom, dateTo)

        return (
            query
            .group_by(Competency.IdCompetency, Competency.nameCompetency)
            .order_by(
                func.count(distinct(Attendance.IdAttendance)).desc(),
                Competency.nameCompetency.asc(),
            )
            .all()
        )
    
    def _eventDurationHoursExpression(self):
        return (func.time_to_sec(func.timediff(Event.endTimeEvent, Event.startTimeEvent)) / 3600)

    def _getDistinctAttendancePairsSubquery(self, eventIdsQuery, aliasName: str):
        return (
            self.db.query(
                Attendance.IdEvent.label("IdEvent"),
                Attendance.IdAttendancePerson.label("IdAttendancePerson"),
            )
            .filter(Attendance.IdEvent.in_(eventIdsQuery))
            .distinct()
            .subquery(aliasName)
        )

    def _getAttendanceHoursSummary(self, eventIdsQuery, aliasPrefix: str):
        attendancePairs = self._getDistinctAttendancePairsSubquery(
            eventIdsQuery,
            f"{aliasPrefix}AttendancePairs",
        )
        personSolutionCenter = SolutionCenter.__table__.alias(
            f"{aliasPrefix}PersonSolutionCenter"
        )
        internalPersonCondition = (
            func.lower(func.trim(personSolutionCenter.c.nameSolutionCenter))
            != self.EXTERNAL_SOLUTION_CENTER_NAME
        )
        durationHours = self._eventDurationHoursExpression()

        result = (
            self.db.query(
                func.count(
                    distinct(
                        case(
                            (
                                internalPersonCondition,
                                AttendancePerson.IdAttendancePerson,
                            )
                        )
                    )
                ).label("totalInternalTrainedPeople"),
                func.coalesce(
                    func.sum(durationHours),
                    0,
                ).label("totalTrainingHours"),
                func.coalesce(
                    func.sum(
                        case(
                            (internalPersonCondition, durationHours),
                            else_=0,
                        )
                    ),
                    0,
                ).label("totalInternalTrainingHours"),
            )
            .select_from(attendancePairs)
            .join(Event, Event.IdEvent == attendancePairs.c.IdEvent)
            .join(
                AttendancePerson,
                AttendancePerson.IdAttendancePerson
                == attendancePairs.c.IdAttendancePerson,
            )
            .outerjoin(
                personSolutionCenter,
                personSolutionCenter.c.IdSolutionCenter
                == AttendancePerson.IdSolutionCenter,
            )
            .first()
        )

        return {
            "totalInternalTrainedPeople": int(
                result.totalInternalTrainedPeople or 0
            ),
            "totalTrainingHours": round(
                float(result.totalTrainingHours or 0),
                2,
            ),
            "totalInternalTrainingHours": round(
                float(result.totalInternalTrainingHours or 0),
                2,
            ),
        }

    def _getInternalTrainingByCollaborator(
        self,
        eventIdsQuery,
        totalHoursLabel: str,
        aliasPrefix: str,
    ):
        attendancePairs = self._getDistinctAttendancePairsSubquery(
            eventIdsQuery,
            f"{aliasPrefix}AttendancePairs",
        )
        personSolutionCenter = SolutionCenter.__table__.alias(
            f"{aliasPrefix}PersonSolutionCenter"
        )

        return (
            self.db.query(
                AttendancePerson.documentNumberAttendancePerson.label(
                    "documentNumberAttendancePerson"
                ),
                AttendancePerson.fullNameAttendancePerson.label(
                    "fullNameAttendancePerson"
                ),
                personSolutionCenter.c.nameSolutionCenter.label(
                    "nameSolutionCenter"
                ),
                func.coalesce(
                    func.sum(self._eventDurationHoursExpression()),
                    0,
                ).label(totalHoursLabel),
            )
            .select_from(attendancePairs)
            .join(Event, Event.IdEvent == attendancePairs.c.IdEvent)
            .join(
                AttendancePerson,
                AttendancePerson.IdAttendancePerson
                == attendancePairs.c.IdAttendancePerson,
            )
            .outerjoin(
                personSolutionCenter,
                personSolutionCenter.c.IdSolutionCenter
                == AttendancePerson.IdSolutionCenter,
            )
            .filter(
                func.lower(func.trim(personSolutionCenter.c.nameSolutionCenter))
                != self.EXTERNAL_SOLUTION_CENTER_NAME
            )
            .group_by(
                AttendancePerson.IdAttendancePerson,
                AttendancePerson.documentNumberAttendancePerson,
                AttendancePerson.fullNameAttendancePerson,
                personSolutionCenter.c.nameSolutionCenter,
            )
            .order_by(
                func.sum(self._eventDurationHoursExpression()).desc(),
                AttendancePerson.fullNameAttendancePerson.asc(),
            )
            .all()
        )

    def _getSstEventIdsQuery(
        self,
        dateFrom: Optional[date],
        dateTo: Optional[date],
    ):
        eventSolutionCenter = SolutionCenter.__table__.alias(
            "sstEventSolutionCenter"
        )
        query = (
            self.db.query(Event.IdEvent)
            .select_from(Event)
            .join(
                eventSolutionCenter,
                eventSolutionCenter.c.IdSolutionCenter
                == Event.IdSolutionCenter,
            )
            .filter(
                func.lower(func.trim(eventSolutionCenter.c.nameSolutionCenter))
                == self.SST_SOLUTION_CENTER_NAME
            )
        )

        return self._applyDateFilters(query, dateFrom, dateTo).distinct()

    def getSstTrainingSummary(self, dateFrom: Optional[date], dateTo: Optional[date],):
        summary = self._getAttendanceHoursSummary(
            self._getSstEventIdsQuery(dateFrom, dateTo),
            "sstSummary",
        )

        return {
            "totalInternalSstTrainedPeople": summary[
                "totalInternalTrainedPeople"
            ],
            "totalSstTrainingHours": summary["totalTrainingHours"],
        }

    def getSstTrainingByCollaborator(self, dateFrom: Optional[date], dateTo: Optional[date],):
        return self._getInternalTrainingByCollaborator(
            self._getSstEventIdsQuery(dateFrom, dateTo),
            "totalSstTrainingHours",
            "sstCollaborator",
        )

    def _getThematicEventIdsQuery(
        self,
        themeKey: str,
        dateFrom: Optional[date],
        dateTo: Optional[date],
    ):
        normalizedThemeKey = themeKey.strip().upper()

        if normalizedThemeKey not in self.THEMATIC_TRAINING_KEYS:
            raise ValueError("El tipo de reporte temático no es válido.")

        query = self.db.query(Event.IdEvent).select_from(Event)

        if normalizedThemeKey == "INOCUIDAD":
            eventSolutionCenter = SolutionCenter.__table__.alias(
                "thematicEventSolutionCenter"
            )
            query = query.join(
                eventSolutionCenter,
                eventSolutionCenter.c.IdSolutionCenter == Event.IdSolutionCenter,
            ).filter(
                func.lower(func.trim(eventSolutionCenter.c.nameSolutionCenter))
                == self.QUALITY_SOLUTION_CENTER_NAME
            )
        elif normalizedThemeKey == "SERVICIO":
            query = (
                query
                .join(EventCompetency, EventCompetency.IdEvent == Event.IdEvent)
                .join(
                    Competency,
                    Competency.IdCompetency == EventCompetency.IdCompetency,
                )
                .filter(
                    func.lower(func.trim(Competency.nameCompetency))
                    == self.SERVICE_COMPETENCY_NAME
                )
            )
        elif normalizedThemeKey in {"PRODUCTO", "SER"}:
            programName = (
                self.PROGRAM_HACER_NAME
                if normalizedThemeKey == "PRODUCTO"
                else self.PROGRAM_SER_NAME
            )
            query = query.join(
                SpecificTrainingProgram,
                SpecificTrainingProgram.IdSpecificTrainingProgram
                == Event.IdSpecificTrainingProgram,
            ).filter(
                func.lower(
                    func.trim(
                        SpecificTrainingProgram.nameSpecificTrainingProgram
                    )
                )
                == programName
            )
        else:
            query = query.join(
                AssistanceReason,
                AssistanceReason.IdAssistanceReason == Event.IdAssistanceReason,
            ).filter(
                func.lower(func.trim(AssistanceReason.nameAssistanceReason))
                == self.INDUCTION_ASSISTANCE_REASON_NAME
            )

        return self._applyDateFilters(query, dateFrom, dateTo).distinct()

    def getThematicTrainingSummary(
        self,
        themeKey: str,
        dateFrom: Optional[date],
        dateTo: Optional[date],
    ):
        return self._getAttendanceHoursSummary(
            self._getThematicEventIdsQuery(themeKey, dateFrom, dateTo),
            f"thematic{themeKey.strip().title()}Summary",
        )

    def getThematicTrainingByCollaborator(
        self,
        themeKey: str,
        dateFrom: Optional[date],
        dateTo: Optional[date],
    ):
        return self._getInternalTrainingByCollaborator(
            self._getThematicEventIdsQuery(themeKey, dateFrom, dateTo),
            "totalTrainingHours",
            f"thematic{themeKey.strip().title()}Collaborator",
        )

    def getThematicTrainingByTopic(
        self,
        themeKey: str,
        dateFrom: Optional[date],
        dateTo: Optional[date],
    ):
        normalizedThemeKey = themeKey.strip().upper()

        if normalizedThemeKey not in {"PRODUCTO", "SER"}:
            return []

        eventIdsQuery = self._getThematicEventIdsQuery(
            normalizedThemeKey,
            dateFrom,
            dateTo,
        )

        return (
            self.db.query(
                EventTopic.nameEventTopic.label("nameEventTopic"),
                func.count(distinct(Event.IdEvent)).label("totalTrainings"),
                func.count(
                    distinct(AttendancePerson.IdAttendancePerson)
                ).label("totalTrainedPeople"),
            )
            .select_from(EventTopic)
            .join(Event, Event.IdEvent == EventTopic.IdEvent)
            .outerjoin(Attendance, Attendance.IdEvent == Event.IdEvent)
            .outerjoin(
                AttendancePerson,
                AttendancePerson.IdAttendancePerson
                == Attendance.IdAttendancePerson,
            )
            .filter(Event.IdEvent.in_(eventIdsQuery))
            .group_by(EventTopic.nameEventTopic)
            .order_by(
                func.count(distinct(Event.IdEvent)).desc(),
                EventTopic.nameEventTopic.asc(),
            )
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

    def getTransversalTrainingSummary(self, dateFrom: Optional[date], dateTo: Optional[date],):
        query = (
            self.db.query(
                func.coalesce(
                    func.sum(self._eventDurationHoursExpression()),
                    0,
                ).label("totalTransversalTrainingHours"),
                func.count(
                    distinct(AttendancePerson.IdAttendancePerson)
                ).label("totalTransversalTrainingPeople"),
            )
            .select_from(Event)
            .join(
                AssistanceReason,
                AssistanceReason.IdAssistanceReason == Event.IdAssistanceReason,
            )
            .join(Attendance, Attendance.IdEvent == Event.IdEvent)
            .join(
                AttendancePerson,
                AttendancePerson.IdAttendancePerson == Attendance.IdAttendancePerson,
            )
            .filter(
                func.lower(func.trim(AssistanceReason.nameAssistanceReason))
                == self.TRANSVERSAL_ASSISTANCE_REASON_NAME
            )
        )

        query = self._applyDateFilters(query, dateFrom, dateTo)
        result = query.first()

        return {
            "totalTransversalTrainingHours": round(float(result.totalTransversalTrainingHours or 0), 2),
            "totalTransversalTrainingPeople": int(result.totalTransversalTrainingPeople or 0),
        }

    def getTransversalTrainingByCollaborator(self, dateFrom: Optional[date], dateTo: Optional[date],):
        personSolutionCenter = SolutionCenter.__table__.alias("transversalPersonSolutionCenter")

        query = (
            self.db.query(
                AttendancePerson.documentNumberAttendancePerson.label("documentNumberAttendancePerson"),
                AttendancePerson.fullNameAttendancePerson.label("fullNameAttendancePerson"),
                personSolutionCenter.c.nameSolutionCenter.label("nameSolutionCenter"),
                func.coalesce(
                    func.sum(self._eventDurationHoursExpression()),
                    0,
                ).label("totalTransversalTrainingHours"),
            )
            .select_from(Event)
            .join(
                AssistanceReason,
                AssistanceReason.IdAssistanceReason == Event.IdAssistanceReason,
            )
            .join(Attendance, Attendance.IdEvent == Event.IdEvent)
            .join(
                AttendancePerson,
                AttendancePerson.IdAttendancePerson == Attendance.IdAttendancePerson,
            )
            .outerjoin(
                personSolutionCenter,
                personSolutionCenter.c.IdSolutionCenter == AttendancePerson.IdSolutionCenter,
            )
            .filter(
                func.lower(func.trim(AssistanceReason.nameAssistanceReason))
                == self.TRANSVERSAL_ASSISTANCE_REASON_NAME
            )
        )

        query = self._applyDateFilters(query, dateFrom, dateTo)

        return (
            query
            .group_by(
                AttendancePerson.IdAttendancePerson,
                AttendancePerson.documentNumberAttendancePerson,
                AttendancePerson.fullNameAttendancePerson,
                personSolutionCenter.c.nameSolutionCenter,
            )
            .order_by(
                func.sum(self._eventDurationHoursExpression()).desc(),
                AttendancePerson.fullNameAttendancePerson.asc(),
            )
            .all()
        )
    
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
            "averageTrainingHoursPerWorker": round(averageTrainingHoursPerWorker, 4),
        }

    def getCollaboratorTrainingHistory(self, search: str, dateFrom: Optional[date], dateTo: Optional[date],):
        eventSolutionCenter = SolutionCenter.__table__.alias("historyEventSolutionCenter")
        personSolutionCenter = SolutionCenter.__table__.alias("historyPersonSolutionCenter")
        normalizedSearch = " ".join(search.strip().lower().split())
        searchTokens = normalizedSearch.split()
        normalizedName = func.lower(
            func.trim(AttendancePerson.fullNameAttendancePerson)
        )
        normalizedDocument = func.lower(
            func.trim(AttendancePerson.documentNumberAttendancePerson)
        )
        searchConditions = [
            or_(
                normalizedName.like(f"%{token}%"),
                normalizedDocument.like(f"%{token}%"),
            )
            for token in searchTokens
        ]

        query = (
            self.db.query(
                AttendancePerson.IdAttendancePerson.label("IdAttendancePerson"),
                AttendancePerson.documentNumberAttendancePerson.label("documentNumberAttendancePerson"),
                AttendancePerson.fullNameAttendancePerson.label("fullNameAttendancePerson"),
                personSolutionCenter.c.nameSolutionCenter.label("personSolutionCenterName"),
                Event.IdEvent.label("IdEvent"),
                Event.titleEvent.label("titleEvent"),
                Event.dateEvent.label("dateEvent"),
                eventSolutionCenter.c.nameSolutionCenter.label("trainingSolutionCenterName"),
                self._eventDurationHoursExpression().label("trainingHours"),
            )
            .select_from(Attendance)
            .join(Event, Event.IdEvent == Attendance.IdEvent)
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
            .filter(and_(*searchConditions))
            .distinct()
        )

        query = self._applyDateFilters(query, dateFrom, dateTo)

        return query.order_by(
            AttendancePerson.fullNameAttendancePerson.asc(),
            Event.dateEvent.desc(),
            Event.titleEvent.asc(),
        ).all()
