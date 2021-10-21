ATTACHMENTS := $(shell python scripts/download_attachments.py)

upload_% : merged/%.pdf
	aws s3

merged/%.pdf : $(addsuffix .pdf,$(basename $(ATTACHMENTS)))
	# This assumes that if a file is already a PDF, it does not need to be
	# converted. We have a block in our code that reconverts "PDFs with a little
	# extra garbage", but I have no idea what that means, nor do I know if it
	# will be an issue when merging with Poppler instead of the Python library.
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
