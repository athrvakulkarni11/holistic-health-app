"""
Generate a sample blood work / lab report PDF for testing the upload feature.
Uses fpdf2 library to create a realistic-looking lab report.
"""
from fpdf import FPDF
from datetime import datetime


class LabReportPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(0, 102, 153)
        self.cell(0, 10, "HealthFirst Diagnostics", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, "123 Medical Center Blvd, Suite 200  |  New Delhi, India  |  Ph: +91 11 2345 6789", align="C", new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 5, "NABL Accredited  |  CAP Certified  |  ISO 15189:2022", align="C", new_x="LMARGIN", new_y="NEXT")
        self.line(10, self.get_y() + 3, 200, self.get_y() + 3)
        self.ln(8)

    def footer(self):
        self.set_y(-20)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(140, 140, 140)
        self.cell(0, 5, "This report is generated for informational purposes. Please consult your physician for interpretation.", align="C", new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 5, f"Page {self.page_no()}/{{nb}}  |  Report ID: RPT-2026-00847", align="C")


def generate_report():
    pdf = LabReportPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()

    # Patient Information
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(0, 102, 153)
    pdf.cell(0, 8, "PATIENT INFORMATION", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(0, 102, 153)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(50, 50, 50)

    info = [
        ("Patient Name", "Rahul Sharma"),
        ("Age / Gender", "42 Years / Male"),
        ("Patient ID", "PID-2026-10432"),
        ("Referred By", "Dr. Priya Mehta, MD (Internal Medicine)"),
        ("Collection Date", "February 12, 2026, 07:30 AM (Fasting)"),
        ("Report Date", "February 13, 2026"),
    ]

    for label, value in info:
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(45, 6, f"{label}:", new_x="END")
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 6, value, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(6)

    # Test Results
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(0, 102, 153)
    pdf.cell(0, 8, "LABORATORY TEST RESULTS", new_x="LMARGIN", new_y="NEXT")
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    # Table header
    def table_header(section_name):
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(230, 242, 250)
        pdf.set_text_color(0, 80, 120)
        pdf.cell(0, 7, f"  {section_name}", fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(80, 80, 80)
        pdf.set_fill_color(245, 245, 245)
        pdf.cell(60, 6, "  Test Name", border="B", fill=True, new_x="END")
        pdf.cell(30, 6, "Result", border="B", fill=True, align="C", new_x="END")
        pdf.cell(25, 6, "Unit", border="B", fill=True, align="C", new_x="END")
        pdf.cell(45, 6, "Reference Range", border="B", fill=True, align="C", new_x="END")
        pdf.cell(30, 6, "Status", border="B", fill=True, align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    def table_row(test, result, unit, ref_range, status="Normal"):
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(60, 6, f"  {test}", new_x="END")

        if status == "HIGH":
            pdf.set_text_color(200, 50, 50)
            pdf.set_font("Helvetica", "B", 9)
        elif status == "LOW":
            pdf.set_text_color(200, 130, 0)
            pdf.set_font("Helvetica", "B", 9)
        else:
            pdf.set_text_color(50, 50, 50)

        pdf.cell(30, 6, str(result), align="C", new_x="END")

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(25, 6, unit, align="C", new_x="END")
        pdf.cell(45, 6, ref_range, align="C", new_x="END")

        if status == "HIGH":
            pdf.set_text_color(200, 50, 50)
            pdf.set_font("Helvetica", "B", 8)
        elif status == "LOW":
            pdf.set_text_color(200, 130, 0)
            pdf.set_font("Helvetica", "B", 8)
        else:
            pdf.set_text_color(0, 150, 80)
            pdf.set_font("Helvetica", "", 8)

        pdf.cell(30, 6, status, align="C", new_x="LMARGIN", new_y="NEXT")

    # COMPLETE BLOOD COUNT
    table_header("COMPLETE BLOOD COUNT (CBC)")
    table_row("Hemoglobin", "13.2", "g/dL", "13.5 - 17.5", "LOW")
    table_row("RBC Count", "4.3", "million/mcL", "4.5 - 5.5", "LOW")
    table_row("WBC Count", "7200", "cells/mcL", "4000 - 11000", "Normal")
    table_row("Platelet Count", "245000", "cells/mcL", "150000 - 400000", "Normal")
    table_row("Hematocrit (PCV)", "39.8", "%", "40 - 54", "LOW")
    table_row("MCV", "88.2", "fL", "80 - 100", "Normal")
    table_row("MCH", "28.5", "pg", "27 - 33", "Normal")
    pdf.ln(4)

    # IRON STUDIES
    table_header("IRON STUDIES & VITAMINS")
    table_row("Ferritin", "15", "ng/mL", "20 - 250", "LOW")
    table_row("Serum Iron", "45", "mcg/dL", "60 - 170", "LOW")
    table_row("Vitamin B12", "180", "pg/mL", "200 - 900", "LOW")
    table_row("Vitamin D (25-OH)", "16.5", "ng/mL", "30 - 100", "LOW")
    table_row("Folic Acid", "8.2", "ng/mL", "3.0 - 17.0", "Normal")
    pdf.ln(4)

    # METABOLIC PANEL
    table_header("METABOLIC PANEL")
    table_row("Fasting Glucose", "118", "mg/dL", "70 - 100", "HIGH")
    table_row("HbA1c", "6.2", "%", "4.0 - 5.6", "HIGH")
    table_row("Fasting Insulin", "18.5", "uIU/mL", "2.6 - 24.9", "Normal")
    table_row("Blood Urea Nitrogen (BUN)", "16", "mg/dL", "7 - 20", "Normal")
    table_row("Creatinine", "0.9", "mg/dL", "0.7 - 1.3", "Normal")
    table_row("Uric Acid", "6.8", "mg/dL", "3.5 - 7.2", "Normal")
    pdf.ln(4)

    # LIPID PROFILE
    table_header("LIPID PROFILE")
    table_row("Total Cholesterol", "235", "mg/dL", "< 200", "HIGH")
    table_row("LDL Cholesterol", "155", "mg/dL", "< 100", "HIGH")
    table_row("HDL Cholesterol", "38", "mg/dL", "> 40", "LOW")
    table_row("Triglycerides", "195", "mg/dL", "< 150", "HIGH")
    table_row("VLDL Cholesterol", "39", "mg/dL", "< 30", "HIGH")
    table_row("Total Cholesterol/HDL Ratio", "6.18", "", "< 5.0", "HIGH")
    pdf.ln(4)

    # New page for remaining tests
    pdf.add_page()

    # INFLAMMATORY MARKERS
    table_header("INFLAMMATORY MARKERS")
    table_row("hs-CRP", "3.8", "mg/L", "< 1.0", "HIGH")
    table_row("ESR", "22", "mm/hr", "0 - 15", "HIGH")
    pdf.ln(4)

    # THYROID PANEL
    table_header("THYROID FUNCTION TESTS")
    table_row("TSH", "5.2", "mIU/L", "0.4 - 4.0", "HIGH")
    table_row("Free T4", "0.9", "ng/dL", "0.8 - 1.8", "Normal")
    table_row("Free T3", "2.4", "pg/mL", "2.3 - 4.2", "Normal")
    pdf.ln(4)

    # LIVER FUNCTION
    table_header("LIVER FUNCTION TESTS")
    table_row("SGPT / ALT", "52", "U/L", "7 - 56", "Normal")
    table_row("SGOT / AST", "38", "U/L", "5 - 40", "Normal")
    table_row("Alkaline Phosphatase", "78", "U/L", "44 - 147", "Normal")
    table_row("Total Bilirubin", "0.8", "mg/dL", "0.1 - 1.2", "Normal")
    table_row("GGT", "45", "U/L", "9 - 48", "Normal")
    table_row("Total Protein", "7.2", "g/dL", "6.0 - 8.3", "Normal")
    table_row("Albumin", "4.1", "g/dL", "3.5 - 5.5", "Normal")
    pdf.ln(6)

    # Summary & Comments
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(0, 102, 153)
    pdf.cell(0, 8, "CLINICAL OBSERVATIONS", new_x="LMARGIN", new_y="NEXT")
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(50, 50, 50)

    observations = [
        "1. Mild anemia (low hemoglobin, RBC, and hematocrit) likely due to iron deficiency - ferritin and serum iron are both below normal.",
        "2. Vitamin B12 deficiency detected (180 pg/mL). Supplementation recommended.",
        "3. Significant Vitamin D insufficiency (16.5 ng/mL). Oral supplementation of 60,000 IU weekly for 8 weeks advised.",
        "4. Prediabetic range: Fasting glucose (118 mg/dL) and HbA1c (6.2%) both elevated. Dietary intervention and lifestyle modification recommended.",
        "5. Dyslipidemia: Elevated total cholesterol, LDL, triglycerides, and VLDL with low HDL. Cardiovascular risk assessment recommended.",
        "6. Elevated hs-CRP (3.8 mg/L) indicates systemic inflammation - may be related to metabolic syndrome.",
        "7. Subclinical hypothyroidism: TSH mildly elevated (5.2 mIU/L) with normal Free T4 and T3. Monitoring recommended.",
        "8. Liver function tests within acceptable limits but SGPT trending toward upper range.",
    ]

    for obs in observations:
        pdf.multi_cell(0, 5, obs)
        pdf.ln(2)

    pdf.ln(4)

    # Doctor's Notes
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(0, 102, 153)
    pdf.cell(0, 8, "RECOMMENDATIONS", new_x="LMARGIN", new_y="NEXT")
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(50, 50, 50)

    recommendations = [
        "- Iron supplementation: Ferrous sulfate 325mg daily with Vitamin C for enhanced absorption",
        "- Vitamin B12: Methylcobalamin 1500 mcg daily for 3 months",
        "- Vitamin D3: 60,000 IU weekly for 8 weeks, then maintenance dose of 1000 IU daily",
        "- Dietary changes: Mediterranean diet pattern, reduce refined carbohydrates and saturated fats",
        "- Regular aerobic exercise: 150 minutes/week of moderate intensity",
        "- Repeat lipid profile and HbA1c in 3 months",
        "- Thyroid function recheck in 6 weeks",
        "- Consider oral glucose tolerance test (OGTT) for detailed diabetes screening",
    ]

    for rec in recommendations:
        pdf.multi_cell(0, 5, rec)
        pdf.ln(1)

    pdf.ln(8)

    # Signature
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(95, 5, "Verified By:", new_x="END")
    pdf.cell(95, 5, "Approved By:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(95, 5, "Dr. Sanjay Kumar, MD Pathology", new_x="END")
    pdf.cell(95, 5, "Dr. Anita Verma, MD Biochemistry", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(95, 5, "Reg. No: MCI-28347", new_x="END")
    pdf.cell(95, 5, "Reg. No: MCI-31892", new_x="LMARGIN", new_y="NEXT")

    # Save
    output_path = "sample_lab_report.pdf"
    pdf.output(output_path)
    print(f"Sample lab report generated: {output_path}")
    print("File contains realistic biomarker data with several abnormal values:")
    print("  Low: Hemoglobin, RBC, Ferritin, Iron, Vitamin B12, Vitamin D, HDL")
    print("  High: Fasting Glucose, HbA1c, Total Cholesterol, LDL, Triglycerides, hs-CRP, TSH")
    print("Use this file to test the Upload feature of HolisticAI!")


if __name__ == "__main__":
    generate_report()
