from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AppLesson,
    AppLessonClip,
    AppLessonTranscriptBlock,
    AppLessonVocabulary,
    AppLineAccount,
    AppTutorMessage,
    AppTutorSession,
    AppUser,
    AppVocabItem,
    AppVocabReviewHistory,
    AppVideo,
)
from app.services.constants import TUTOR_ACTIONS, loc, status_label
from app.services.security import hash_password


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def ensure_seed_data(db: AsyncSession) -> AppUser:
    existing_user = (
        await db.execute(select(AppUser).where(AppUser.username == "alex").limit(1))
    ).scalar_one_or_none()
    if existing_user:
        return existing_user

    now = _utc_now()
    user = AppUser(
        id="user-alex",
        username="alex",
        password_hash=hash_password("sorbet-demo"),
        full_name="Alex Rivera",
        email="alex@example.com",
        avatar_initials="AR",
        membership_tier="plus",
        native_language_id="thai",
        target_language_id="french",
        level_id="intermediate",
        weekly_focus_id="steady",
        interests=["conversation", "listening"],
        streak_days=11,
        daily_goal_minutes=20,
        timezone="Asia/Bangkok",
        app_locale="en",
        goal_summary=loc(
            "Reach confident conversational French from short YouTube lessons.",
            "พัฒนาภาษาฝรั่งเศสเชิงสนทนาอย่างมั่นใจจากบทเรียน YouTube แบบสั้น",
        ),
        notification_preferences={
            "practiceReminders": True,
            "weeklyDigest": True,
            "tutorFollowUps": False,
        },
        tutor_preferences={
            "voiceId": "sorbet",
            "modeId": "coach",
            "autoPlayPronunciation": True,
        },
        created_at=now - timedelta(days=90),
        updated_at=now - timedelta(minutes=15),
    )
    db.add(user)

    line_account = AppLineAccount(
        id="line-account-alex",
        user_id=user.id,
        line_user_id="line-user-123",
        display_name="Alex on LINE",
        status_message="Practicing French one bite at a time.",
        picture_accent="coral",
        language="en",
        last_synced_at=now - timedelta(minutes=2),
        created_at=now - timedelta(days=30),
        updated_at=now - timedelta(minutes=2),
    )
    db.add(line_account)

    lessons = [
        AppLesson(
            id="lesson-paris-bistro",
            user_id=user.id,
            source_url="https://www.youtube.com/watch?v=mock-paris-bistro",
            title=loc("Paris bistro listening lab", "ห้องฝึกฟัง Paris bistro"),
            subtitle=loc("The art of the perfect crêpe", "ศิลปะของเครปที่สมบูรณ์แบบ"),
            duration_seconds=755,
            progress_percent=72,
            status_id="in_progress",
            status_label=status_label("in_progress"),
            extracted_vocab_count=18,
            category_id="conversation",
            thumbnail_accent="coral",
            clip_count=6,
            source_label=loc("YouTube import", "นำเข้าจาก YouTube"),
            learning_objectives=[
                loc(
                    "Notice how French speakers soften explanations with `nous allons` and descriptive adjectives.",
                    "สังเกตว่าผู้พูดภาษาฝรั่งเศสทำให้คำอธิบายนุ่มนวลขึ้นด้วย `nous allons` และคำคุณศัพท์เชิงบรรยายอย่างไร",
                ),
                loc(
                    "Practice culinary vocabulary that appears naturally in travel and food videos.",
                    "ฝึกคำศัพท์ด้านอาหารที่ปรากฏอย่างเป็นธรรมชาติในวิดีโอท่องเที่ยวและอาหาร",
                ),
            ],
            tabs=[
                {"id": "source", "label": loc("Source", "ต้นฉบับ")},
                {"id": "translated", "label": loc("Translated", "แปล")},
                {"id": "dual", "label": loc("Dual", "สองภาษา")},
            ],
            recommended_actions=[
                {
                    "id": "to-tutor",
                    "labelKey": "common.actions.askTutor",
                    "href": "/tutor?lessonId=lesson-paris-bistro",
                },
                {
                    "id": "to-vocab",
                    "labelKey": "common.actions.extractVocab",
                    "href": "/vocab?lessonId=lesson-paris-bistro",
                },
            ],
            source_language_id="french",
            target_language_id="thai",
            voice_id="sorbet",
            auto_detect=True,
            last_activity_at=now - timedelta(hours=2),
            created_at=now - timedelta(days=5),
            updated_at=now - timedelta(hours=2),
        ),
        AppLesson(
            id="lesson-night-market-chat",
            user_id=user.id,
            source_url="https://www.youtube.com/watch?v=mock-night-market",
            title=loc("Night market survival phrases", "วลีเอาตัวรอดในตลาดกลางคืน"),
            subtitle=loc(
                "Polite questions for prices, portions, and directions",
                "คำถามสุภาพสำหรับราคา ปริมาณ และเส้นทาง",
            ),
            duration_seconds=588,
            progress_percent=24,
            status_id="ready",
            status_label=status_label("ready"),
            extracted_vocab_count=12,
            category_id="travel",
            thumbnail_accent="sky",
            clip_count=4,
            source_label=loc("YouTube import", "นำเข้าจาก YouTube"),
            learning_objectives=[
                loc(
                    "Practice useful travel questions that are short, polite, and easy to adapt in real situations.",
                    "ฝึกคำถามสำหรับการเดินทางที่สั้น สุภาพ และปรับใช้ได้ง่ายในสถานการณ์จริง",
                ),
                loc(
                    "Spot tone markers that make requests sound warmer instead of abrupt.",
                    "สังเกตคำหรือโทนที่ทำให้คำขอฟังดูเป็นมิตรขึ้นแทนที่จะห้วน",
                ),
            ],
            tabs=[
                {"id": "source", "label": loc("Source", "ต้นฉบับ")},
                {"id": "translated", "label": loc("Translated", "แปล")},
                {"id": "dual", "label": loc("Dual", "สองภาษา")},
            ],
            recommended_actions=[
                {
                    "id": "to-tutor",
                    "labelKey": "common.actions.askTutor",
                    "href": "/tutor?lessonId=lesson-night-market-chat",
                },
                {
                    "id": "to-vocab",
                    "labelKey": "common.actions.extractVocab",
                    "href": "/vocab?lessonId=lesson-night-market-chat",
                },
            ],
            source_language_id="english",
            target_language_id="thai",
            voice_id="sorbet",
            auto_detect=True,
            last_activity_at=now - timedelta(hours=6),
            created_at=now - timedelta(hours=6),
            updated_at=now - timedelta(hours=6),
        ),
        AppLesson(
            id="lesson-office-small-talk",
            user_id=user.id,
            source_url="https://www.youtube.com/watch?v=mock-office-small-talk",
            title=loc("Office small talk booster", "ตัวช่วย small talk ในออฟฟิศ"),
            subtitle=loc(
                "Casual phrases for meetings, breaks, and quick updates",
                "วลีสบาย ๆ สำหรับการประชุม ช่วงพัก และอัปเดตสั้น ๆ",
            ),
            duration_seconds=670,
            progress_percent=100,
            status_id="completed",
            status_label=status_label("completed"),
            extracted_vocab_count=8,
            category_id="work",
            thumbnail_accent="mint",
            clip_count=5,
            source_label=loc("YouTube import", "นำเข้าจาก YouTube"),
            learning_objectives=[
                loc(
                    "Build confidence with quick workplace phrases that sound natural in hybrid teams.",
                    "สร้างความมั่นใจกับวลีสั้น ๆ ในที่ทำงานที่ฟังดูเป็นธรรมชาติสำหรับทีมแบบไฮบริด",
                ),
                loc(
                    "Notice how speakers soften opinions before giving updates.",
                    "สังเกตว่าผู้พูดทำให้ความคิดเห็นฟังนุ่มนวลขึ้นก่อนให้ข้อมูลอัปเดตอย่างไร",
                ),
            ],
            tabs=[
                {"id": "source", "label": loc("Source", "ต้นฉบับ")},
                {"id": "translated", "label": loc("Translated", "แปล")},
                {"id": "dual", "label": loc("Dual", "สองภาษา")},
            ],
            recommended_actions=[
                {
                    "id": "to-tutor",
                    "labelKey": "common.actions.askTutor",
                    "href": "/tutor?lessonId=lesson-office-small-talk",
                },
                {
                    "id": "to-vocab",
                    "labelKey": "common.actions.extractVocab",
                    "href": "/vocab?lessonId=lesson-office-small-talk",
                },
            ],
            source_language_id="english",
            target_language_id="thai",
            voice_id="atelier",
            auto_detect=True,
            last_activity_at=now - timedelta(days=1),
            created_at=now - timedelta(days=8),
            updated_at=now - timedelta(days=1),
        ),
    ]
    for lesson in lessons:
        db.add(lesson)

    clips = [
        AppLessonClip(
            id="clip-youtube-paris",
            lesson_id="lesson-paris-bistro",
            source_url="https://www.youtube.com/watch?v=mock-paris-bistro",
            title=loc(
                "French gastronomy: The art of the perfect crêpe",
                "ศาสตร์อาหารฝรั่งเศส: ศิลปะของเครปที่สมบูรณ์แบบ",
            ),
            channel="Le Petit Chef",
            duration_seconds=755,
            transcript_status="ready",
            seq=1,
            created_at=now - timedelta(days=5),
            updated_at=now - timedelta(hours=2),
        ),
        AppLessonClip(
            id="clip-night-market-chat",
            lesson_id="lesson-night-market-chat",
            source_url="https://www.youtube.com/watch?v=mock-night-market",
            title=loc(
                "Night market survival phrases",
                "วลีเอาตัวรอดในตลาดกลางคืน",
            ),
            channel="Travel Thai Lab",
            duration_seconds=588,
            transcript_status="ready",
            seq=1,
            created_at=now - timedelta(hours=6),
            updated_at=now - timedelta(hours=6),
        ),
        AppLessonClip(
            id="clip-office-small-talk",
            lesson_id="lesson-office-small-talk",
            source_url="https://www.youtube.com/watch?v=mock-office-small-talk",
            title=loc("Office small talk booster", "ตัวช่วย small talk ในออฟฟิศ"),
            channel="Hybrid Teams Daily",
            duration_seconds=670,
            transcript_status="ready",
            seq=1,
            created_at=now - timedelta(days=8),
            updated_at=now - timedelta(days=1),
        ),
    ]
    for clip in clips:
        db.add(clip)

    transcript_blocks = [
        AppLessonTranscriptBlock(
            id="block-1",
            lesson_id="lesson-paris-bistro",
            clip_id="clip-youtube-paris",
            seq=1,
            timestamp_label="00:12",
            source="Bonjour tout le monde, aujourd'hui nous allons explorer Paris ensemble.",
            translated="Hello everyone, today we are going to explore Paris together.",
            explanation=loc(
                "A warm opener that uses the future-near form `nous allons`.",
                "เป็นการเปิดบทสนทนาอย่างเป็นกันเองด้วยโครงสร้างอนาคตใกล้ `nous allons`",
            ),
        ),
        AppLessonTranscriptBlock(
            id="block-2",
            lesson_id="lesson-paris-bistro",
            clip_id="clip-youtube-paris",
            seq=2,
            timestamp_label="02:45",
            source="Le Louvre est l'un des plus grands musées du monde.",
            translated="The Louvre is one of the largest museums in the world.",
            explanation=loc(
                "Use this structure to compare landmarks, dishes, or neighborhoods.",
                "ใช้โครงสร้างนี้เพื่อเปรียบเทียบสถานที่ อาหาร หรือย่านต่าง ๆ ได้",
            ),
        ),
        AppLessonTranscriptBlock(
            id="block-3",
            lesson_id="lesson-paris-bistro",
            clip_id="clip-youtube-paris",
            seq=3,
            timestamp_label="05:28",
            source="C'est un endroit magnifique rempli d'histoire et d'art.",
            translated="It is a magnificent place filled with history and art.",
            explanation=loc(
                "The adjective `magnifique` adds an enthusiastic but natural tone.",
                "คำคุณศัพท์ `magnifique` ช่วยเพิ่มอารมณ์ชื่นชมอย่างเป็นธรรมชาติ",
            ),
        ),
        AppLessonTranscriptBlock(
            id="block-4",
            lesson_id="lesson-night-market-chat",
            clip_id="clip-night-market-chat",
            seq=1,
            timestamp_label="00:08",
            source="Excuse me, how much is this grilled squid?",
            translated="ขอโทษนะ อันนี้ปลาหมึกย่างราคาเท่าไหร่คะ",
            explanation=loc(
                "This opener is polite and direct, which is useful for crowded market settings.",
                "ประโยคเปิดนี้สุภาพและตรงประเด็น เหมาะกับสถานการณ์ในตลาดที่คนพลุกพล่าน",
            ),
        ),
        AppLessonTranscriptBlock(
            id="block-5",
            lesson_id="lesson-night-market-chat",
            clip_id="clip-night-market-chat",
            seq=2,
            timestamp_label="02:16",
            source="Can you make it a little less spicy for me?",
            translated="ช่วยทำให้เผ็ดน้อยลงหน่อยได้ไหมคะ",
            explanation=loc(
                "Adding `a little` keeps the request soft and easy to accept.",
                "การเติมคำว่า `หน่อย` หรือ `เล็กน้อย` ช่วยให้คำขอฟังนุ่มนวลขึ้น",
            ),
        ),
        AppLessonTranscriptBlock(
            id="block-6",
            lesson_id="lesson-office-small-talk",
            clip_id="clip-office-small-talk",
            seq=1,
            timestamp_label="00:21",
            source="Just a quick heads-up, the client pushed the deadline by two days.",
            translated="แจ้งให้ทราบสั้น ๆ ว่าลูกค้าเลื่อนเดดไลน์ออกไปอีกสองวัน",
            explanation=loc(
                "This phrase is common in internal updates because it sounds efficient but not abrupt.",
                "วลีนี้พบบ่อยในการอัปเดตงานภายใน เพราะฟังดูรวดเร็วแต่ไม่ห้วนเกินไป",
            ),
        ),
        AppLessonTranscriptBlock(
            id="block-7",
            lesson_id="lesson-office-small-talk",
            clip_id="clip-office-small-talk",
            seq=2,
            timestamp_label="03:11",
            source="I can take the first pass if that helps the team move faster.",
            translated="ฉันช่วยรับช่วงแรกให้ได้ ถ้ามันช่วยให้ทีมเดินหน้าได้เร็วขึ้น",
            explanation=loc(
                "Use this to volunteer without sounding too forceful.",
                "ใช้ประโยคนี้เมื่อต้องการอาสาช่วยโดยไม่ทำให้ฟังดูแข็งหรือกดดันเกินไป",
            ),
        ),
    ]
    for block in transcript_blocks:
        db.add(block)

    lesson_vocab = [
        AppLessonVocabulary(
            id="lesson-vocab-louvre",
            lesson_id="lesson-paris-bistro",
            term="Louvre",
            pronunciation="/luvr/",
            meaning=loc(
                "A world-famous art museum in Paris, France.",
                "พิพิธภัณฑ์ศิลปะชื่อดังระดับโลกในกรุงปารีส ประเทศฝรั่งเศส",
            ),
        ),
        AppLessonVocabulary(
            id="lesson-vocab-ensemble",
            lesson_id="lesson-paris-bistro",
            term="ensemble",
            pronunciation="/ɑ̃.sɑ̃bl/",
            meaning=loc("Together, as a group or shared activity.", "ร่วมกัน หรือทำบางอย่างไปด้วยกัน"),
        ),
        AppLessonVocabulary(
            id="lesson-vocab-spicy",
            lesson_id="lesson-night-market-chat",
            term="spicy",
            pronunciation="/spai-see/",
            meaning=loc(
                "Food that has a lot of heat from chili or pepper.",
                "อาหารที่มีความเผ็ดจากพริกหรือเครื่องเทศ",
            ),
        ),
        AppLessonVocabulary(
            id="lesson-vocab-portion",
            lesson_id="lesson-night-market-chat",
            term="portion",
            pronunciation="/por-shun/",
            meaning=loc("A serving size or amount of food.", "ปริมาณอาหารต่อหนึ่งเสิร์ฟ"),
        ),
        AppLessonVocabulary(
            id="lesson-vocab-heads-up",
            lesson_id="lesson-office-small-talk",
            term="heads-up",
            pronunciation="/hedz-up/",
            meaning=loc("A quick warning or advance notice.", "การแจ้งเตือนหรือบอกล่วงหน้าแบบสั้น ๆ"),
        ),
        AppLessonVocabulary(
            id="lesson-vocab-first-pass",
            lesson_id="lesson-office-small-talk",
            term="first pass",
            pronunciation="/furst-pas/",
            meaning=loc(
                "The first draft or initial attempt at a task.",
                "ฉบับร่างแรกหรือการลองทำครั้งแรกของงาน",
            ),
        ),
    ]
    for vocab in lesson_vocab:
        db.add(vocab)

    tutor_sessions = [
        AppTutorSession(
            id="session-paris-bistro",
            user_id=user.id,
            lesson_id="lesson-paris-bistro",
            clip_id="clip-youtube-paris",
            title=loc("Chef vocabulary support", "ตัวช่วยคำศัพท์เชฟ"),
            lesson_label=loc("Paris bistro listening lab", "ห้องฝึกฟัง Paris bistro"),
            last_message_preview=loc(
                "Try saying `une pincée de sel` with a softer French `r`.",
                "ลองพูด `une pincée de sel` โดยออกเสียง `r` แบบฝรั่งเศสให้นุ่มขึ้น",
            ),
            mode_id="coach",
            context_summary=loc(
                "The selected lesson focuses on descriptive food language, soft explanations, and common French kitchen vocabulary.",
                "บทเรียนที่เลือกเน้นภาษาบรรยายอาหาร การอธิบายอย่างนุ่มนวล และคำศัพท์ครัวภาษาฝรั่งเศสที่ใช้บ่อย",
            ),
            selected_excerpt="In the video, the chef says `Je mets une pincée de sel dans mon omelette.`",
            quick_prompts=[
                "Explain `une pincée`",
                "Quiz me on kitchen words",
                "Translate this naturally",
            ],
            waveform=[4, 7, 10, 13, 8, 6, 3],
            available_actions=TUTOR_ACTIONS,
            created_at=now - timedelta(days=5),
            updated_at=now - timedelta(minutes=15),
        ),
        AppTutorSession(
            id="session-night-market",
            user_id=user.id,
            lesson_id="lesson-night-market-chat",
            clip_id="clip-night-market-chat",
            title=loc("Travel phrase coach", "โค้ชวลีการเดินทาง"),
            lesson_label=loc("Night market survival phrases", "วลีเอาตัวรอดในตลาดกลางคืน"),
            last_message_preview=loc(
                "Want a shorter version of your pricing question?",
                "อยากได้เวอร์ชันสั้นลงของคำถามเรื่องราคาไหม",
            ),
            mode_id="pronunciation",
            context_summary=loc(
                "This lesson trains polite travel phrases for prices, spice level, and finding directions in crowded public places.",
                "บทเรียนนี้ฝึกวลีสุภาพสำหรับถามราคา ระดับความเผ็ด และขอเส้นทางในที่สาธารณะที่คนหนาแน่น",
            ),
            selected_excerpt="Can you make it a little less spicy for me?",
            quick_prompts=[
                "Make this more polite",
                "Give me a shorter version",
                "Practice pronunciation",
            ],
            waveform=[3, 5, 9, 12, 8, 5, 2],
            available_actions=TUTOR_ACTIONS,
            created_at=now - timedelta(hours=6),
            updated_at=now - timedelta(hours=1),
        ),
        AppTutorSession(
            id="session-office-small-talk",
            user_id=user.id,
            lesson_id="lesson-office-small-talk",
            clip_id="clip-office-small-talk",
            title=loc("Meeting language tutor", "ติวเตอร์ภาษาสำหรับการประชุม"),
            lesson_label=loc("Office small talk booster", "ตัวช่วย small talk ในออฟฟิศ"),
            last_message_preview=loc(
                "I can help you sound more natural in update calls.",
                "ฉันช่วยให้คุณฟังเป็นธรรมชาติมากขึ้นเวลาอัปเดตงานได้",
            ),
            mode_id="grammar",
            context_summary=loc(
                "The clip focuses on short update phrases, volunteering help, and sounding collaborative in workplace conversations.",
                "คลิปนี้เน้นวลีอัปเดตสั้น ๆ การอาสาช่วย และการทำให้บทสนทนาในที่ทำงานฟังดูร่วมมือกันมากขึ้น",
            ),
            selected_excerpt="Just a quick heads-up, the client pushed the deadline by two days.",
            quick_prompts=[
                "Make this sound warmer",
                "Explain `heads-up`",
                "Quiz me on work phrases",
            ],
            waveform=[5, 6, 9, 11, 7, 5, 4],
            available_actions=TUTOR_ACTIONS,
            created_at=now - timedelta(days=8),
            updated_at=now - timedelta(days=1),
        ),
    ]
    for session in tutor_sessions:
        db.add(session)

    tutor_messages = [
        AppTutorMessage(
            id="assistant-1",
            session_id="session-paris-bistro",
            role="assistant",
            text="In this clip, `une pincée` means a pinch. It is the natural cooking phrase French speakers use for small amounts of seasoning.",
            timestamp_label="Sorbet AI",
            created_at=now - timedelta(minutes=20),
        ),
        AppTutorMessage(
            id="user-1",
            session_id="session-paris-bistro",
            role="user",
            text="How can I use it outside cooking?",
            timestamp_label="15m ago",
            created_at=now - timedelta(minutes=15),
        ),
        AppTutorMessage(
            id="assistant-2",
            session_id="session-paris-bistro",
            role="assistant",
            text="Usually you keep it in cooking contexts. For general small amounts, you would choose different nouns depending on what you are measuring.",
            timestamp_label="Sorbet AI",
            created_at=now - timedelta(minutes=14),
        ),
        AppTutorMessage(
            id="assistant-3",
            session_id="session-night-market",
            role="assistant",
            text="That sentence works well because `a little` softens the request. It makes the vendor more likely to help without feeling commanded.",
            timestamp_label="Sorbet AI",
            created_at=now - timedelta(hours=1, minutes=5),
        ),
        AppTutorMessage(
            id="user-2",
            session_id="session-night-market",
            role="user",
            text="Can you give me a faster version for real conversations?",
            timestamp_label="1h ago",
            created_at=now - timedelta(hours=1),
        ),
        AppTutorMessage(
            id="assistant-4",
            session_id="session-night-market",
            role="assistant",
            text="Sure. You can shorten it to `Less spicy, please.` It is still polite and much easier to remember on the spot.",
            timestamp_label="Sorbet AI",
            created_at=now - timedelta(hours=1, minutes=1),
        ),
        AppTutorMessage(
            id="assistant-5",
            session_id="session-office-small-talk",
            role="assistant",
            text="`Heads-up` is a friendly way to warn someone or give advance notice. It is informal but extremely common at work.",
            timestamp_label="Sorbet AI",
            created_at=now - timedelta(days=1, minutes=20),
        ),
        AppTutorMessage(
            id="user-3",
            session_id="session-office-small-talk",
            role="user",
            text="Would it sound okay in a client call too?",
            timestamp_label="Yesterday",
            created_at=now - timedelta(days=1, minutes=10),
        ),
        AppTutorMessage(
            id="assistant-6",
            session_id="session-office-small-talk",
            role="assistant",
            text="For some clients, yes. If you want a safer option, say `Just a quick update` instead.",
            timestamp_label="Sorbet AI",
            created_at=now - timedelta(days=1, minutes=9),
        ),
    ]
    for message in tutor_messages:
        db.add(message)

    vocab_items = [
        AppVocabItem(
            id="vocab-pincee",
            user_id=user.id,
            source_lesson_id="lesson-paris-bistro",
            term="une pincée",
            translation=loc("a pinch", "หยิบมือหนึ่ง / หยิบเล็กน้อย"),
            pronunciation="/yn pan-sey/",
            status_id="due",
            due_at=now,
            example="Je mets une pincée de sel dans mon omelette.",
            notes=loc("Usually used in cooking or recipes for tiny amounts.", "มักใช้ในบริบทการทำอาหารหรือสูตรอาหารสำหรับปริมาณเล็กน้อย"),
            interval_days=1,
            repetitions=1,
            created_at=now - timedelta(days=4),
            updated_at=now - timedelta(hours=2),
        ),
        AppVocabItem(
            id="vocab-heads-up",
            user_id=user.id,
            source_lesson_id="lesson-office-small-talk",
            term="heads-up",
            translation=loc("advance notice", "การแจ้งล่วงหน้า"),
            pronunciation="/hedz-up/",
            status_id="mastered",
            due_at=now + timedelta(days=10),
            example="Just a quick heads-up, the client moved the deadline.",
            notes=loc(
                "Friendly and informal. Safer alternatives exist for formal clients.",
                "เป็นกันเองและไม่เป็นทางการมากนัก ถ้าคุยกับลูกค้าแบบทางการอาจใช้คำอื่นแทน",
            ),
            interval_days=10,
            repetitions=4,
            created_at=now - timedelta(days=8),
            updated_at=now - timedelta(days=1),
        ),
        AppVocabItem(
            id="vocab-less-spicy",
            user_id=user.id,
            source_lesson_id="lesson-night-market-chat",
            term="less spicy",
            translation=loc("less spicy", "เผ็ดน้อยลง"),
            pronunciation="/les spai-see/",
            status_id="due",
            due_at=now,
            example="Can you make it a little less spicy for me?",
            notes=loc(
                "A practical phrase for street food and travel contexts.",
                "เป็นวลีที่ใช้ได้จริงในบริบทอาหารริมทางและการเดินทาง",
            ),
            interval_days=1,
            repetitions=1,
            created_at=now - timedelta(days=1),
            updated_at=now - timedelta(hours=6),
        ),
        AppVocabItem(
            id="vocab-first-pass",
            user_id=user.id,
            source_lesson_id="lesson-office-small-talk",
            term="first pass",
            translation=loc("first draft", "ฉบับร่างแรก"),
            pronunciation="/furst-pas/",
            status_id="difficult",
            due_at=now + timedelta(days=1),
            example="I can take the first pass if that helps.",
            notes=loc(
                "Common in project work and collaborative tasks.",
                "พบบ่อยในการทำโปรเจกต์และการทำงานร่วมกัน",
            ),
            interval_days=2,
            repetitions=1,
            created_at=now - timedelta(days=8),
            updated_at=now - timedelta(days=1),
        ),
        AppVocabItem(
            id="vocab-ensemble",
            user_id=user.id,
            source_lesson_id="lesson-paris-bistro",
            term="ensemble",
            translation=loc("together", "ร่วมกัน"),
            pronunciation="/ɑ̃-sɑ̃bl/",
            status_id="mastered",
            due_at=now + timedelta(days=14),
            example="Aujourd'hui nous allons explorer Paris ensemble.",
            notes=loc(
                "Useful for inclusive speaking in everyday narration.",
                "มีประโยชน์สำหรับการพูดแบบชวนอีกฝ่ายมีส่วนร่วมในชีวิตประจำวัน",
            ),
            interval_days=14,
            repetitions=5,
            created_at=now - timedelta(days=5),
            updated_at=now - timedelta(hours=2),
        ),
    ]
    for item in vocab_items:
        db.add(item)

    review_history = [
        AppVocabReviewHistory(
            id=f"review-{idx}",
            vocab_item_id="vocab-pincee" if idx < 4 else "vocab-less-spicy",
            user_id=user.id,
            answer="good",
            previous_status_id="due",
            next_status_id="due",
            next_due_at=now + timedelta(days=idx % 4 + 1),
            created_at=now - timedelta(hours=idx),
        )
        for idx in range(1, 8)
    ]
    for row in review_history:
        db.add(row)

    video = AppVideo(
        id="video-paris-bistro",
        lesson_id="lesson-paris-bistro",
        title=loc("Walking tour: Le Marais", "ทัวร์เดินชม Le Marais"),
        thumbnail_accent="coral",
        duration_seconds=902,
        summary=loc(
            "A warm cultural walk packed with travel vocabulary and descriptive grammar.",
            "ทัวร์วัฒนธรรมที่เต็มไปด้วยคำศัพท์ท่องเที่ยวและไวยากรณ์เชิงพรรณนา",
        ),
        quiz=[
            {
                "id": "quiz-1",
                "prompt": loc(
                    "What does 'une pincée' most naturally mean in the lesson?",
                    "คำว่า 'une pincée' ในบทเรียนหมายถึงอะไรอย่างเป็นธรรมชาติที่สุด?",
                ),
                "options": [
                    {"id": "a", "label": loc("A pinch", "หยิบมือ / หยิบเล็กน้อย"), "correct": True},
                    {"id": "b", "label": loc("A spoon", "ช้อน"), "correct": False},
                    {"id": "c", "label": loc("A plate", "จาน"), "correct": False},
                ],
                "rationale": loc(
                    "French cooking often uses 'une pincée de sel' when seasoning by hand.",
                    "การทำอาหารฝรั่งเศสมักใช้ 'une pincée de sel' เมื่อต้องการใส่เกลือด้วยปลายนิ้ว",
                ),
            },
            {
                "id": "quiz-2",
                "prompt": loc(
                    "Which structure makes the sentence sound descriptive and elevated?",
                    "โครงสร้างใดทำให้ประโยคฟังดูพรรณนาและยกระดับ?",
                ),
                "options": [
                    {"id": "a", "label": loc("l'un des plus grands"), "correct": True},
                    {"id": "b", "label": loc("très petit"), "correct": False},
                    {"id": "c", "label": loc("peu de"), "correct": False},
                ],
                "rationale": loc(
                    "This superlative phrase is common in travel narration and recommendations.",
                    "วลีขั้นสุดยอดนี้พบบ่อยในงานบรรยายการท่องเที่ยวและการแนะนำสถานที่",
                ),
            },
        ],
        created_at=now - timedelta(days=5),
        updated_at=now - timedelta(days=1),
    )
    db.add(video)

    await db.commit()
    await db.refresh(user)
    return user
