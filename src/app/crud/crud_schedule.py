import datetime
from typing import Optional

from sqlalchemy import and_, delete, func
from sqlalchemy.dialects.postgresql import array
from sqlalchemy.future import select

from app import utils
from app.db.connection import get_session
from app.models import (
    Group,
    Institute,
    Lesson,
    LessonCall,
    LessonType,
    Room,
    ScheduleCampus,
    ScheduleDegree,
    ScheduleDiscipline,
    SchedulePeriod,
    Teacher,
    lessons_to_teachers,
)
from app.schemas import (
    CampusCreate,
    DegreeCreate,
    DisciplineCreate,
    GroupCreate,
    InstituteCreate,
    LessonCallCreate,
    LessonCreate,
    LessonDelete,
    LessonTypeCreate,
    PeriodCreate,
    RoomCreate,
    TeacherCreate,
)


async def get_or_create_period(cmd: PeriodCreate):
    async with get_session() as session:
        res = await session.execute(
            select(SchedulePeriod)
            .where(
                and_(
                    SchedulePeriod.year_start == cmd.year_start,
                    SchedulePeriod.year_end == cmd.year_end,
                    SchedulePeriod.semester == cmd.semester,
                )
            )
            .limit(1)
        )
        period = res.scalar()
        if not period:
            period = SchedulePeriod(**cmd.dict())
            session.add(period)
            await session.commit()
            await session.refresh(period)
        return period


async def get_or_create_degree(cmd: DegreeCreate):
    async with get_session() as session:
        res = await session.execute(
            select(ScheduleDegree).where(ScheduleDegree.name == cmd.name).limit(1)
        )
        degree = res.scalar()
        if not degree:
            degree = ScheduleDegree(**cmd.dict())
            session.add(degree)
            await session.commit()
            await session.refresh(degree)
        return degree


async def get_or_create_institute(cmd: InstituteCreate):
    async with get_session() as session:
        res = await session.execute(
            select(Institute).where(Institute.name == cmd.name).limit(1)
        )
        institute = res.scalar()
        if not institute:
            institute = Institute(**cmd.dict())
            session.add(institute)
            await session.commit()
            await session.refresh(institute)
        return institute


async def get_or_create_group(cmd: GroupCreate):
    async with get_session() as session:
        res = await session.execute(
            select(Group)
            .where(
                and_(
                    Group.name == cmd.name,
                    Group.degree_id == cmd.degree_id,
                    Group.institute_id == cmd.institute_id,
                )
            )
            .limit(1)
        )
        group = res.scalar()
        if not group:
            group = Group(**cmd.dict())
            session.add(group)
            await session.commit()
            await session.refresh(group)
        return group


async def get_or_create_lesson_type(cmd: LessonTypeCreate):
    async with get_session() as session:
        res = await session.execute(
            select(LessonType).where(LessonType.name == cmd.name).limit(1)
        )
        lesson_type = res.scalar()
        if not lesson_type:
            lesson_type = LessonType(**cmd.dict())
            session.add(lesson_type)
            await session.commit()
            await session.refresh(lesson_type)
        return lesson_type


async def get_or_create_campus(cmd: CampusCreate):
    async with get_session() as session:
        res = await session.execute(
            select(ScheduleCampus).where(ScheduleCampus.name == cmd.name).limit(1)
        )
        campus = res.scalar()
        if not campus:
            campus = ScheduleCampus(**cmd.dict())
            session.add(campus)
            await session.commit()
            await session.refresh(campus)
        return campus


async def get_or_create_room(cmd: RoomCreate):
    async with get_session() as session:
        res = await session.execute(select(Room).where(Room.name == cmd.name).limit(1))
        room = res.scalar()
        if not room:
            room = Room(**cmd.dict())
            session.add(room)
            await session.commit()
            await session.refresh(room)
        return room


async def get_or_create_discipline(cmd: DisciplineCreate):
    async with get_session() as session:
        res = await session.execute(
            select(ScheduleDiscipline)
            .where(ScheduleDiscipline.name == cmd.name)
            .limit(1)
        )
        discipline = res.scalar()
        if not discipline:
            discipline = ScheduleDiscipline(**cmd.dict())
            session.add(discipline)
            await session.commit()
            await session.refresh(discipline)
        return discipline


async def get_or_create_teacher(cmd: TeacherCreate):
    async with get_session() as session:
        res = await session.execute(
            select(Teacher).where(Teacher.name == cmd.name).limit(1)
        )
        teacher = res.scalar()
        if not teacher:
            teacher = Teacher(**cmd.dict())
            session.add(teacher)
            await session.commit()
            await session.refresh(teacher)
        return teacher


async def get_or_create_lesson_call(cmd: LessonCallCreate):
    async with get_session() as session:
        res = await session.execute(
            select(LessonCall)
            .where(
                and_(
                    LessonCall.time_start == cmd.time_start,
                    LessonCall.time_end == cmd.time_end,
                    LessonCall.num == cmd.num,
                )
            )
            .limit(1)
        )
        lesson_call = res.scalar()
        if not lesson_call:
            lesson_call = LessonCall(**cmd.dict())
            session.add(lesson_call)
            await session.commit()
            await session.refresh(lesson_call)
        return lesson_call


async def get_or_create_lesson(cmd: LessonCreate):
    async with get_session() as session:
        res = await session.execute(
            select(Lesson)
            .join(lessons_to_teachers)
            .where(
                and_(
                    lessons_to_teachers.c.teacher_id.in_(cmd.teachers_id),
                    Lesson.lesson_type_id == cmd.lesson_type_id,
                    Lesson.group_id == cmd.group_id,
                    Lesson.discipline_id == cmd.discipline_id,
                    Lesson.room_id == cmd.room_id,
                    Lesson.weeks == array(cmd.weeks),
                    Lesson.call_id == cmd.call_id,
                    Lesson.subgroup == cmd.subgroup,
                )
            )
            .limit(1)
        )
        lesson = res.scalar()
        if not lesson:
            lesson = Lesson(**cmd.dict(exclude={"teachers_id", "weeks"}))

            # insert list of weeks to lesson (postgres array)
            lesson.weeks = array(cmd.weeks)

            session.add(lesson)
            await session.flush()
            for teacher_id in cmd.teachers_id:
                await session.execute(
                    lessons_to_teachers.insert().values(
                        lesson_id=lesson.id, teacher_id=teacher_id
                    )
                )
            await session.commit()
            await session.refresh(lesson)

        return lesson


async def get_groups():
    async with get_session() as session:
        res = await session.execute(select(Group))
        return res.scalars().all()


async def get_group(name: str) -> Group:
    async with get_session() as session:
        res = await session.execute(select(Group).where(Group.name == name).limit(1))
        return res.scalar()


async def clear_group_schedule(name: str):
    async with get_session() as session:
        await session.execute(
            delete(Lesson).where(
                Lesson.group_id == select(Group.id).where(Group.name == name)
            )
        )
        await session.commit()


async def delete_lesson(cmd: LessonDelete):
    async with get_session() as session:
        await session.execute(
            select(Lesson)
            .where(
                and_(
                    Lesson.group_id == select(Group.id).where(Group.name == cmd.group),
                    Lesson.call_id
                    == select(LessonCall.id).where(
                        LessonCall.time_start == cmd.time_start,
                        LessonCall.time_end == cmd.time_end,
                        LessonCall.num == cmd.num,
                    ),
                    Lesson.weekday == cmd.weekday,
                )
            )
            .execution_options(synchronize_session=False)
        )
        await session.commit()


async def get_lessons_by_teacher(teacher_id: int):
    async with get_session() as session:
        res = await session.execute(
            select(Lesson)
            .join(lessons_to_teachers)
            .where(lessons_to_teachers.c.teacher_id == teacher_id)
        )
        return res.scalars().all()


async def search_tachers(name: str):
    async with get_session() as session:
        res = await session.execute(
            select(Teacher).where(func.lower(Teacher.name).contains(name.lower()))
        )
        return res.scalars().all()


async def get_lessons_by_room(room_id: int):
    async with get_session() as session:
        res = await session.execute(select(Lesson).where(Lesson.room_id == room_id))
        return res.scalars().all()


async def search_rooms(name: str) -> list[Room]:
    async with get_session() as session:
        res = await session.execute(
            select(Room).where(func.lower(Room.name).contains(name.lower()))
        )
        return res.scalars().all()


async def get_room(name: str, campus_short_name: Optional[str] = None):
    async with get_session() as session:
        res = await session.execute(
            select(Room)
            .where(
                and_(
                    Room.name == name,
                    Room.campus_id
                    == select(ScheduleCampus.id).where(
                        ScheduleCampus.short_name == campus_short_name
                    ),
                )
            )
            .limit(1)
        )
        return res.scalar()


async def get_lessons_by_room(room_id: int) -> list[Lesson]:
    async with get_session() as session:
        res = await session.execute(
            select(Lesson)
            .where(Lesson.room_id == room_id)
            .order_by(Lesson.weekday, Lesson.call_id)
        )
        return res.scalars().all()


async def get_lessons_by_room_and_date(room_id: int, date: datetime.date) -> list[Lesson]:
    week = utils.get_week(date=date)

    async with get_session() as session:
        res = await session.execute(
            select(Lesson)
            .where(
                and_(
                    Lesson.room_id == room_id,
                    Lesson.weeks.contains([week]),
                    Lesson.weekday == date.weekday(),
                )
            )
            .order_by(Lesson.call_id)
        )
        return res.scalars().all()


async def get_lessons_by_room_and_week(room_id: int, week: int) -> list[Lesson]:
    async with get_session() as session:
        res = await session.execute(
            select(Lesson)
            .where(
                and_(
                    Lesson.room_id == room_id,
                    Lesson.weeks.contains([week]),
                )
            )
            .order_by(Lesson.weekday, Lesson.call_id)
        )
        return res.scalars().all()


async def get_room_workload(room_id: int):
    async with get_session() as session:
        # get all lessons for room
        res = await session.execute(
            select(Lesson)
            .where(Lesson.room_id == room_id)
            .order_by(Lesson.weekday, Lesson.call_id)
        )
        lessons = res.scalars().all()

        # get all calls
        res = await session.execute(select(LessonCall))
        calls = res.scalars().all()

        checked = []
        workload = 0
        for lesson in lessons:
            for week in lesson.weeks:
                for call in calls:
                    # Внимание! У одной аудитории может быть несколько групп в одно и то же время (например, лекции и лабораторные)
                    if (
                            call.id == lesson.call_id
                            and (
                            lesson.weekday,
                            lesson.call_id,
                            week,
                    )
                            not in checked
                    ):
                        workload += 1
                        checked.append((lesson.weekday, lesson.call_id, week))

        return workload / (6 * 6 * 16) * 100


async def get_campuses() -> list[ScheduleCampus]:
    async with get_session() as session:
        res = await session.execute(select(ScheduleCampus))
        return res.scalars().all()


async def get_campus_rooms(campus_id: int) -> list[Room]:
    async with get_session() as session:
        res = await session.execute(
            select(Room)
            .where(Room.campus_id == campus_id)
            .order_by(func.lower(Room.name).asc())
        )
        return res.scalars().all()

