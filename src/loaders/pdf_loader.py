"""Advanced PDF document loader for GraphRAG project.

This module provides comprehensive PDF processing capabilities including:
- Text extraction
- Table extraction
- OCR for scanned documents
- Image and diagram processing
"""

import os
from typing import Any

import cv2
import fitz  # PyMuPDF
import numpy as np
import pytesseract
import tabula
from pdf2image import convert_from_path


class PDFLoader:
    """Advanced loader for PDF documents."""

    @staticmethod
    def load(file_path: str) -> tuple[str, dict[str, Any]]:
        """Load a PDF document with advanced processing.

        Args:
            file_path: Path to the PDF file

        Returns:
            Tuple of (text, metadata)

        """
        # Extract metadata
        metadata = PDFLoader._extract_metadata(file_path)

        # Extract text content
        text_content = PDFLoader._extract_text(file_path)

        # Extract tables
        tables_text = PDFLoader._extract_tables(file_path)

        # Perform OCR if needed
        if not text_content.strip():
            ocr_text = PDFLoader._perform_ocr(file_path)
            text_content = ocr_text

        # Combine all text
        combined_text = text_content

        # Add tables if found
        if tables_text:
            combined_text += "\n\n" + tables_text

        # Add file metadata
        metadata.update(
            {
                "title": metadata.get(
                    "title", os.path.splitext(os.path.basename(file_path))[0]
                ),
                "source": "PDF File",
                "file_path": file_path,
            }
        )

        return combined_text, metadata

    @staticmethod
    def _extract_metadata(file_path: str) -> dict[str, Any]:
        """Extract metadata from PDF.

        Args:
            file_path: Path to the PDF file

        Returns:
            Extracted metadata

        """
        metadata = {}

        try:
            # Open the PDF
            doc = fitz.open(file_path)

            # Extract document info
            info = doc.metadata

            # Map PDF metadata to our format
            if info:
                if info.get("title"):
                    metadata["title"] = info["title"]
                if info.get("author"):
                    metadata["author"] = info["author"]
                if info.get("subject"):
                    metadata["subject"] = info["subject"]
                if info.get("keywords"):
                    metadata["keywords"] = info["keywords"]
                if info.get("creator"):
                    metadata["creator"] = info["creator"]
                if info.get("producer"):
                    metadata["producer"] = info["producer"]

            # Add page count
            metadata["page_count"] = len(doc)

            # Close the document
            doc.close()

        except Exception as e:
            print(f"Error extracting PDF metadata: {e}")

        return metadata

    @staticmethod
    def _extract_text(file_path: str) -> str:
        """Extract text from PDF using PyMuPDF.

        Args:
            file_path: Path to the PDF file

        Returns:
            Extracted text

        """
        text = ""

        try:
            # Open the PDF
            doc = fitz.open(file_path)

            # Extract text from each page
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text = page.get_text("text")
                text += page_text + "\n\n"

            # Close the document
            doc.close()

        except Exception as e:
            print(f"Error extracting PDF text: {e}")

        return text

    @staticmethod
    def _extract_tables(file_path: str) -> str:
        """Extract tables from PDF using tabula-py.

        Args:
            file_path: Path to the PDF file

        Returns:
            Extracted tables as text

        """
        tables_text = ""

        try:
            # Extract all tables from the PDF
            tables = tabula.read_pdf(file_path, pages="all", multiple_tables=True)

            # Convert tables to text
            for i, table in enumerate(tables):
                tables_text += f"Table {i + 1}:\n"
                tables_text += table.to_string() + "\n\n"

        except Exception as e:
            print(f"Error extracting tables from PDF: {e}")

        return tables_text

    @staticmethod
    def _perform_ocr(file_path: str) -> str:
        """Perform OCR on PDF pages.

        Args:
            file_path: Path to the PDF file

        Returns:
            OCR text

        """
        ocr_text = ""

        try:
            # Convert PDF to images
            images = convert_from_path(file_path)

            # Perform OCR on each image
            for i, image in enumerate(images):
                # Convert PIL image to OpenCV format
                img = np.array(image)
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

                # Preprocess image for better OCR results
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[
                    1
                ]

                # Perform OCR
                page_text = pytesseract.image_to_string(gray)
                ocr_text += page_text + "\n\n"

        except Exception as e:
            print(f"Error performing OCR on PDF: {e}")

        return ocr_text

    @staticmethod
    def _detect_diagrams(file_path: str) -> list[dict[str, Any]]:
        """Detect and process diagrams in PDF.

        Args:
            file_path: Path to the PDF file

        Returns:
            List of detected diagrams with descriptions

        """
        diagrams = []

        try:
            # Open the PDF
            doc = fitz.open(file_path)

            # Process each page
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)

                # Extract images
                image_list = page.get_images(full=True)

                # Process each image
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]

                    # Convert to OpenCV format
                    nparr = np.frombuffer(image_bytes, np.uint8)
                    img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                    # Simple heuristic to identify diagrams (can be improved)
                    # Check if the image has certain characteristics of diagrams
                    is_diagram = PDFLoader._is_likely_diagram(img_cv)

                    if is_diagram:
                        diagrams.append(
                            {
                                "page": page_num + 1,
                                "index": img_index,
                                "description": f"Diagram on page {page_num + 1}",
                            }
                        )

            # Close the document
            doc.close()

        except Exception as e:
            print(f"Error detecting diagrams in PDF: {e}")

        return diagrams

    @staticmethod
    def _is_likely_diagram(img) -> bool:
        """Determine if an image is likely to be a diagram.

        Args:
            img: OpenCV image

        Returns:
            True if the image is likely a diagram

        """
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150)

        # Count edge pixels
        edge_pixel_count = np.count_nonzero(edges)

        # Calculate edge density
        total_pixels = edges.shape[0] * edges.shape[1]
        edge_density = edge_pixel_count / total_pixels

        # Diagrams typically have a higher edge density than photos
        # and a more uniform distribution of edges
        return edge_density > 0.05
