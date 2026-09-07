from datetime import date
from types import SimpleNamespace

import pytest

from app.application.services.ReportApplication import ReportApplication


class FakeReportRepository:
    def getGeneralSummary(self, dateFrom, dateTo):
        return {
            "topTrainingSolutionCenterName": "CALIDAD",
            "topTrainingSolutionCenterTotal": 8,
            "totalInternalQualityTrainedPeople": 6,
            "totalInternalSerTrainedPeople": 5,
            "totalInternalHacerTrainedPeople": 7,
        }

    def getThematicTrainingSummary(self, themeKey, dateFrom, dateTo):
        return {
            "totalInternalTrainedPeople": 4,
            "totalTrainingHours": 9,
            "totalInternalTrainingHours": 6,
        }

    def getThematicTrainingByCollaborator(self, themeKey, dateFrom, dateTo):
        return [
            SimpleNamespace(
                documentNumberAttendancePerson="1001",
                fullNameAttendancePerson="COLABORADOR PRUEBA",
                nameSolutionCenter="TECNOLOGÍA",
                totalTrainingHours=2.5,
            )
        ]

    def getThematicTrainingByTopic(self, themeKey, dateFrom, dateTo):
        if themeKey not in {"PRODUCTO", "SER"}:
            return []

        return [
            SimpleNamespace(
                nameEventTopic="BEBIDAS" if themeKey == "PRODUCTO" else "LIDERAZGO",
                totalTrainings=3,
                totalTrainedPeople=12,
            )
        ]


def test_general_report_keeps_only_general_management_indicators():
    service = ReportApplication(FakeReportRepository())

    result = service.getGeneralReport(date(2026, 9, 1), date(2026, 9, 30))

    assert result.totalInternalQualityTrainedPeople == 6
    assert result.totalInternalSerTrainedPeople == 5
    assert result.totalInternalHacerTrainedPeople == 7


def test_thematic_report_builds_all_sections_with_summary_and_details():
    service = ReportApplication(FakeReportRepository())

    result = service.getThematicTrainingReport(
        date(2026, 9, 1),
        date(2026, 9, 30),
    )

    assert [report.key for report in result.reports] == [
        "INOCUIDAD",
        "SERVICIO",
        "PRODUCTO",
        "INDUCCION",
        "SER",
    ]
    assert result.reports[0].summary.totalInternalTrainedPeople == 4
    assert result.reports[0].summary.totalTrainingHours == 9
    assert (
        result.reports[0].summary.averageTrainingHoursPerInternalCollaborator
        == 1.5
    )
    assert result.reports[0].byCollaborator[0].totalTrainingHours == 2.5
    assert result.reports[2].byTopic[0].nameEventTopic == "BEBIDAS"
    assert result.reports[4].byTopic[0].nameEventTopic == "LIDERAZGO"
    assert result.reports[1].byTopic == []


def test_thematic_report_rejects_inverted_date_range():
    service = ReportApplication(FakeReportRepository())

    with pytest.raises(ValueError, match="fecha inicial"):
        service.getThematicTrainingReport(
            date(2026, 9, 30),
            date(2026, 9, 1),
        )


def test_general_report_rejects_inverted_date_range():
    service = ReportApplication(FakeReportRepository())

    with pytest.raises(ValueError, match="fecha inicial"):
        service.getGeneralReport(date(2026, 9, 30), date(2026, 9, 1))
