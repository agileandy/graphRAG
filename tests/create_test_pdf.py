from fpdf import FPDF

# Create PDF
pdf = FPDF()
pdf.add_page()

# Set font
pdf.set_font("Arial", size=12)

# Add title
pdf.set_font("Arial", "B", 16)
pdf.cell(200, 10, txt="GraphRAG: Advanced PDF Processing Test", ln=True, align="C")
pdf.ln(10)

# Add content
pdf.set_font("Arial", size=12)
pdf.multi_cell(
    0,
    10,
    txt="This is a test PDF document for the GraphRAG system. It contains text, a table, and a simple diagram to test the advanced PDF processing capabilities.",
)
pdf.ln(10)

# Add a table
pdf.set_font("Arial", "B", 12)
pdf.cell(200, 10, txt="Table: Document Processing Capabilities", ln=True)
pdf.ln(5)

# Table headers
pdf.set_fill_color(200, 220, 255)
pdf.cell(60, 10, "Document Type", 1, 0, "C", True)
pdf.cell(130, 10, "Processing Features", 1, 1, "C", True)

# Table rows
pdf.set_font("Arial", size=12)
pdf.cell(60, 10, "Text Files (.txt)", 1, 0, "L")
pdf.cell(130, 10, "Basic text extraction", 1, 1, "L")

pdf.cell(60, 10, "JSON Files (.json)", 1, 0, "L")
pdf.cell(130, 10, "Structured data extraction with metadata", 1, 1, "L")

pdf.cell(60, 10, "Markdown Files (.md)", 1, 0, "L")
pdf.cell(130, 10, "Text extraction with frontmatter metadata", 1, 1, "L")

pdf.cell(60, 10, "PDF Files (.pdf)", 1, 0, "L")
pdf.cell(130, 10, "Text, tables, OCR, and diagram detection", 1, 1, "L")
pdf.ln(10)

# Add a simple diagram
pdf.set_font("Arial", "B", 12)
pdf.cell(200, 10, txt="Diagram: GraphRAG System Architecture", ln=True)
pdf.ln(5)

# Draw a simple diagram
pdf.set_line_width(0.5)
pdf.set_draw_color(0, 0, 0)
pdf.set_fill_color(230, 230, 230)

# Draw boxes
# Neo4j box
pdf.rect(40, 180, 60, 20, "DF")
pdf.set_xy(40, 185)
pdf.cell(60, 10, "Neo4j", 0, 1, "C")

# Vector DB box
pdf.rect(140, 180, 60, 20, "DF")
pdf.set_xy(140, 185)
pdf.cell(60, 10, "Vector DB", 0, 1, "C")

# Document Processor box
pdf.rect(90, 130, 60, 20, "DF")
pdf.set_xy(90, 135)
pdf.cell(60, 10, "Processor", 0, 1, "C")

# Draw arrows
pdf.line(120, 150, 70, 180)  # Processor to Neo4j
pdf.line(120, 150, 170, 180)  # Processor to Vector DB

# Save the PDF
pdf.output("test_pdf.pdf")
print("PDF created successfully: test_pdf.pdf")
