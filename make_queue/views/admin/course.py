import io
import xlsxwriter
from django import views
from django.http import HttpResponse

from make_queue.models.course import Printer3DCourse


class CourseXLSXView(views.View):

    def get(self, request):
        # TODO: Fix filtering on course registrations and permissions
        course_registrations = Printer3DCourse.objects.all()

        # Use an in-memory output file, to avoid having to clean up the disk
        output_file = io.BytesIO()

        workbook = xlsxwriter.Workbook(output_file, {"in_memory": True})
        worksheet = workbook.add_worksheet("Kursdeltagere")

        # Styles
        format_header = workbook.add_format({
            "bold": True,
            "font_size": 10,
            "font_name": "Arial",
            "font_color": "#000000",
            "bg_color": "#f8c700",
            "border": 1,
            "border_color": "#000000",
        })

        format_row = workbook.add_format({
            "font_size": 10,
            "font_name": "Arial",
            "font_color": "#000000",
            "bg_color": "#fff2cc",
            "border": 1,
            "border_color": "#000000",
        })

        # Set column width
        worksheet.set_column("A:A", 40)
        worksheet.set_column("B:B", 20)
        worksheet.set_column("C:C", 15)
        worksheet.set_column("D:D", 10)

        # Header
        worksheet.write(0, 0, "Navn", format_header)
        worksheet.write(0, 1, "Brukernavn", format_header)
        worksheet.write(0, 2, "Kortnummer", format_header)
        worksheet.write(0, 3, "Dato", format_header)

        for index, registration in enumerate(course_registrations):
            worksheet.write(index + 1, 0, registration.name, format_row)
            worksheet.write(index + 1, 1, registration.username, format_row)
            worksheet.write_number(index + 1, 2, registration.card_number, format_row)
            worksheet.write(index + 1, 3, registration.date.strftime("%Y-%m-%d"), format_row)

        workbook.close()
        output_file.seek(0)

        response = HttpResponse(output_file.read(),
                                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        response['Content-Disposition'] = 'attachment; filename="Kursdeltagere.xlsx"'

        return response
