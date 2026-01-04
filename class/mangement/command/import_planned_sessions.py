import csv
import re
from django.core.management.base import BaseCommand
from django.db import transaction
from class.models import PlannedSession, SessionStep
from class.models import ClassSection


class Command(BaseCommand):
    help = "Import Day-wise CLAS curriculum CSV into PlannedSession & SessionStep"

    def add_arguments(self, parser):
        parser.add_argument("class_section_id", type=str)
        parser.add_argument("csv_file", type=str)

    # ----------------------------
    # Helpers
    # ----------------------------
    def parse_day_number(self, value):
        """
        "Day 1" → 1
        """
        match = re.search(r"(\d+)", str(value))
        return int(match.group(1)) if match else None

    def parse_duration(self, value):
        """
        "10 Minutes" → 10
        """
        match = re.search(r"(\d+)", str(value))
        return int(match.group(1)) if match else None

    def detect_subject(self, text):
        text = text.lower()

        if "english" in text or "phonic" in text or "abc" in text:
            return "english"
        if "hindi" in text or "varnamala" in text or "vyanjan" in text:
            return "hindi"
        if "math" in text or "number" in text or "table" in text:
            return "maths"
        if "computer" in text or "keyboard" in text or "mouse" in text:
            return "computer"
        if "breathing" in text or "mindfulness" in text or "meditation" in text:
            return "mindfulness"

        return "activity"

    # ----------------------------
    # Main Import
    # ----------------------------
    @transaction.atomic
    def handle(self, *args, **kwargs):
        class_section_id = kwargs["class_section_id"]
        csv_file_path = kwargs["csv_file"]

        class_section = ClassSection.objects.get(id=class_section_id)

        self.stdout.write(self.style.SUCCESS("Starting CLAS curriculum import..."))

        with open(csv_file_path, encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            rows = list(reader)

        current_day = None
        planned_session = None
        step_order = 1

        for row in rows:
            # ----------------------------
            # DAY HEADER
            # ----------------------------
            if row.get("Day"):
                day_number = self.parse_day_number(row["Day"])

                if not day_number:
                    continue

                planned_session, created = PlannedSession.objects.get_or_create(
                    class_section=class_section,
                    day_number=day_number,
                    defaults={
                        "title": row.get("Title") or f"Day {day_number}",
                        "description": "",
                    }
                )

                step_order = 1
                continue

            # ----------------------------
            # ACTIVITY ROW
            # ----------------------------
            if not planned_session:
                continue

            title = (row.get("What") or "").strip()
            description = (row.get("How/What in detail") or "").strip()

            if not title and not description:
                continue

            subject = self.detect_subject(title + " " + description)
            duration = self.parse_duration(row.get("Duration"))

            SessionStep.objects.get_or_create(
                planned_session=planned_session,
                order=step_order,
                defaults={
                    "subject": subject,
                    "title": title or "Activity",
                    "description": description,
                    "duration_minutes": duration,
                }
            )

            step_order += 1

        self.stdout.write(self.style.SUCCESS("✅ Curriculum import completed successfully"))
