ATTACHMENTS := $(shell python scripts/download_attachments.py)

upload_% : merged/%.pdf
	aws s3

merged/%.pdf : $(ATTACHMENTS)
	pdfunite $^ $@

attachments/%.pdf : attachments/%.xlsx
	unoconv -f pdf $<

attachments/%.pdf : attachments/%.doc
	unoconv -f pdf $<

attachments/%.pdf : attachments/%.docx
	unoconv -f pdf $<

attachments/%.pdf : attachments/%.ppt
	unoconv -f pdf $<

attachments/%.pdf : attachments/%.pptx
	unoconv -f pdf $<

attachments/%.pdf : attachments/%.rtf
	unoconv -f pdf $<
