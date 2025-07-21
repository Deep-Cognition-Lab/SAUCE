import json
import sys
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Function to wrap text based on max width
def wrap_text(c, text, margin, max_width):
    lines = []
    words = text.split()
    current_line = ""
    for word in words:
        if c.stringWidth(current_line + " " + word) < max_width:
            current_line += " " + word
        else:
            lines.append(current_line.strip())
            current_line = word
    if current_line:
        lines.append(current_line.strip())
    return lines

# Function to create a chatroom PDF
def create_pdf_from_chat_room(chat_room, config_data, output_filename):
    os.makedirs(os.path.dirname(output_filename), exist_ok=True)

    c = canvas.Canvas(output_filename, pagesize=letter)
    width, height = letter
    y_position = height - 40

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(30, y_position, "Jury Deliberation: Theft Case")
    y_position -= 20

    # Introduction
    c.setFont("Helvetica", 12)
    c.drawString(30, y_position, "Introduction to the Deliberation:")
    y_position -= 15
    intro_text = (
        "The jurors must deliberate on whether the accused is guilty (1) or not guilty (0)."
        "\nEach juror's answer must begin with '1' or '0', followed by an explanation of their decision."
    )
    wrapped_lines = wrap_text(c, intro_text, 30, width - 60)
    for line in wrapped_lines:
        c.drawString(30, y_position, line)
        y_position -= 15
    y_position -= 30

    # Deliberation scenario
    scenario = config_data["experiment"]["scenario"]
    c.setFont("Helvetica-Bold", 12)
    c.drawString(30, y_position, "Deliberation Scenario:")
    y_position -= 15
    wrapped_lines = wrap_text(c, scenario, 30, width - 60)
    c.setFont("Helvetica", 12)
    for line in wrapped_lines:
        c.drawString(30, y_position, line)
        y_position -= 15
    y_position -= 30

    # Process chat entries
    c.setFont("Helvetica", 12)
    for entry in chat_room:
        name = entry["entity"]["name"]
        answer = entry["answer"]

        c.setFont("Helvetica-Bold", 12)
        c.drawString(30, y_position, f"{name}:")
        y_position -= 15

        c.setFont("Helvetica", 12)
        wrapped_lines = wrap_text(c, answer, 30, width - 60)
        for line in wrapped_lines:
            c.drawString(30, y_position, line)
            y_position -= 15

        y_position -= 10

        if y_position < 100:
            c.showPage()
            y_position = height - 40

    c.save()
    print(f"PDF created successfully! Saved as {output_filename}")

if __name__ == "__main__":
    input_filename = sys.argv[1]
    pdf_output_path = sys.argv[2]  # Ensure the full correct path is passed

    # Load JSON data
    with open(input_filename, "r") as f:
        json_data = json.load(f)

    # Extract `chat_room`
    chat_room = json_data.get("chat_room", [])

    # Load configuration
    config_filename = "configurations/vote_guilty_config.json"
    with open(config_filename, "r") as f:
        config_data = json.load(f)

    # Create PDF in the correct location
    create_pdf_from_chat_room(chat_room, config_data, pdf_output_path)
