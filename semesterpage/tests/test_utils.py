from ..models import MainProfile, Semester, StudyProgram


def populate_db():
    fysmat = StudyProgram.objects.get(
        pk=1,
    )

    indmat = MainProfile.objects.create(
        full_name="Industriell matematikk",
        display_name="IndMat",
        study_program=fysmat,
    )

    first_semester = Semester.objects.get(
        number=1,
        study_program=fysmat,
        published=True,
    )

    return {
        'fysmat': fysmat,
        'indmat': indmat,
        'first_semester': first_semester,
    }
