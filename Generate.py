import sys
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape

file_path = 'information.txt'
with open(file_path, 'r') as file:
    lines = file.readlines()
    # Remove newline characters and any leading/trailing whitespaces
    lines = [line.strip() for line in lines]
print(lines[1])

# Read command-line arguments
print(lines[1])
if len(lines) < 18:
    print("Usage: python Generate_Id_Card.py name gender date first_institution second_institution dept position grade member_number issueDate expiryDate line1 line2 line3 line4 address link sign_image_path front_image_path back_image_path")
    sys.exit(1)

c_drive_path = r"C:\photos"

name = lines[1]
gender = lines[2]
date = lines[3]
first_institution = lines[4]
second_institution = lines[5]
dept = lines[6]
position = lines[7]
grade = lines[8]
member_number = lines[9]
# face = c_drive_path + "\\" + member_number + ".jpg"
# barcode = c_drive_path + "\\qr_" + member_number + ".png"
face = "S13133713579.png"
barcode = "qr_\S13133713579.png"
date_issue = lines[10]
date_expiry = lines[11]
line1 = lines[12]
line2 = lines[13]
line3 = lines[14]
line4 = lines[15]
address = lines[16]
link = lines[17]
# sign = c_drive_path + "\\" + lines[18]
# sign = "sign.png"
front_background = lines[19]
back_background = lines[20]
text_color = (0,0,0)


# Load the ID card template image
template = Image.open("front.png")
template = template.resize((520, 330))
# Add user information to the template image
draw = ImageDraw.Draw(template)
font = ImageFont.truetype("arial.ttf", size=15)
title_font = ImageFont.truetype("times new roman bold.ttf", size=15)

#Name
draw.text((40, 100), "Name:", font=title_font, fill=(0, 0, 0))
draw.text((45, 117), name, font=font, fill=(0, 0, 0))
#Gender
draw.text((40, 140), "Gender:", font=title_font, fill=(0, 0, 0))
draw.text((39, 157), gender, font=font, fill=(0, 0, 0))
#Institution
draw.text((40, 180), "Institution:", font=title_font, fill=(0, 0, 0))
draw.text((39, 197), first_institution, font=font, fill=(0, 0, 0))
draw.text((39, 214), second_institution, font=font, fill=(0, 0, 0))
#Institution
draw.text((40, 235), "Dept:", font=title_font, fill=(0, 0, 0))
draw.text((42, 252), dept, font=font, fill=(0, 0, 0))
#Position
draw.text((40, 275), "Position:", font=title_font, fill=(0, 0, 0))
draw.text((41, 292), position, font=font, fill=(0, 0, 0))
#Date
draw.text((235, 140), "Date Of Birth:", font=title_font, fill=(0, 0, 0))
draw.text((235, 157), date, font=font, fill=(0, 0, 0))
#Grade
draw.text((235, 275), "Grade:", font=title_font, fill=(0, 0, 0))
draw.text((235, 292), grade, font=font, fill=(0, 0, 0))

# Load and resize the face image
face_image = Image.open(face)
face_image = face_image.resize((130, 130))

# Paste the face image onto the ID card template
template.paste(face_image, (360, 80))

#mofp_logo = Image.open(c_drive_path + "\\" + "mofp-logo.png")
#mofp_logo = mofp_logo.resize((50,50))

#template.paste(mofp_logo, (430, 15), mofp_logo)

#member_number
draw.text((375, 213), member_number, font=ImageFont.truetype("Poppins-SemiBold.ttf", size=13), fill=(0, 0, 0))

# Load and resize the face image
barcode_image = Image.open(barcode)
barcode_image = barcode_image.resize((90, 90))

# Paste the face image onto the ID card template
template.paste(barcode_image, (380, 230))

destination_front_path = c_drive_path + "\\" + member_number + "id_card_front.png"
# Save the modified template image as a PNG file
template.save(destination_front_path)


# Load the ID card template image
template = Image.open("back-id.png")
template = template.resize((520, 330))

image_width, image_height = template.size
draw = ImageDraw.Draw(template)
font_path = "arialbd.ttf"
font_size = 30
font = ImageFont.truetype(font_path, size=font_size)
title_font = ImageFont.truetype("times new roman bold.ttf", size=17)
content_font = ImageFont.truetype("Roboto-BoldItalic.ttf", size=18)
date_font = ImageFont.truetype("arial.ttf", size=23)

#Date of Issue
draw.text((50, 25), "Date of Issue:", font=title_font, fill=text_color)
draw.text((45, 65), date_issue, font=date_font, fill=text_color)
#Date of Expiry
draw.text((360, 25), "Date of Expiry:", font=title_font, fill=text_color)
draw.text((358, 65), date_expiry, font=date_font, fill=text_color)

# Calculate the width and height of each line of text
_,__,line1_width, line1_height = content_font.getbbox(line1)
_,__,line2_width, line2_height = content_font.getbbox(line2)
_,__,line3_width, line3_height = content_font.getbbox(line3)
_,__,line4_width, line4_height = content_font.getbbox(line4)

# Calculate the starting position for each line of text to center align
x = (image_width - max(line1_width, line2_width, line3_width, line4_width)) // 2
y = (image_height - (line1_height + line2_height + line3_height + line4_height)) // 2

# Create a draw object and add the text lines to the image
draw.text(((image_width - line1_width) // 2, y), line1, font=content_font, fill=text_color, italic=True)
draw.text(((image_width - line2_width) // 2, y + line1_height), line2, font=content_font, fill=text_color, italic=True)
draw.text(((image_width - line3_width) // 2, y + line1_height + line2_height), line3, font=content_font, fill=text_color, italic=True)
draw.text(((image_width - line4_width) // 2, y + line1_height + line2_height + line3_height), line4, font=content_font, fill=text_color, italic=True)

_,__,address_width, address_height = title_font.getbbox(address)

draw.text((275, 234), address, font=title_font, fill=text_color, bold=True)
draw.text((275, 254), link, font=title_font, fill=text_color, bold=True)

#Draw Line
start_point = (250, 220)
end_point = (250, 300)

line_width = 3
draw.line([start_point, end_point], fill=text_color, width=line_width)

# sign_image = Image.open(sign)
# sign_image = sign_image.resize((210, 50))
# signimage_width, signimage_height = sign_image.size
# Paste the face image onto the ID card template
# template.paste(sign_image, (20, 240), sign_image)

destination_back_path = c_drive_path + "\\" + member_number + "_id_card_back.png"

template.save(destination_back_path)
# Generate a PDF file based on the front and back images
destination_pdf_path = c_drive_path + "\\" + member_number + "_id_card.pdf"

# Generate a PDF file based on the front and back images
custom_size = (960, 693)
c = canvas.Canvas(destination_pdf_path, pagesize=landscape(custom_size), bottomup=1, pageCompression=0, verbosity=0, encrypt=None)
#c = canvas.Canvas(destination_pdf_path, pagesize=landscape(custom_size))
c.drawImage(destination_front_path, 0, 0, width=custom_size[0], height=custom_size[1])
c.showPage()

c.drawImage(destination_back_path, 0, 0, width=custom_size[0], height=custom_size[1])
c.showPage()
c.save()

