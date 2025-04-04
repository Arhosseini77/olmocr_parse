import os
import glob
import json
import shutil
import subprocess

# Paths configuration
BASE_SOURCE_DIR = "./ICIS_test_code"      # Root directory for PDFs (can have subfolders)
WORKSPACE_DIR = "./localworkspace"   # Temporary working directory for OCR pipeline
RESULTS_DIR = os.path.join(WORKSPACE_DIR, "results")  # Where OCR pipeline writes JSONL files
BASE_DEST_DIR = "./ICIS_test_code_md"       # Root directory for generated Markdown (mirrors BASE_SOURCE_DIR)

def clear_workspace():
    """Clear the workspace directory completely before processing."""
    if os.path.exists(WORKSPACE_DIR):
        shutil.rmtree(WORKSPACE_DIR)
    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    # Create an empty results folder
    os.makedirs(RESULTS_DIR, exist_ok=True)
    print(f"Cleared and re-created workspace: {WORKSPACE_DIR}")

def run_ocr_pipeline(pdf_files):
    """
    Run the OCR pipeline on the given list of pdf_files.
    The pipeline command uses the WORKSPACE_DIR and expects a list of PDF files.
    """
    # Build the command: pass the workspace and then --pdfs followed by each pdf file.
    cmd = ["python", "-m", "olmocr.pipeline", WORKSPACE_DIR, "--pdfs"] + pdf_files
    print("Running OCR pipeline command:")
    print(" ".join(cmd))
    
    # Run the command
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if process.returncode != 0:
        print("OCR pipeline encountered an error:")
        print(process.stderr)
        return False
    else:
        print("OCR pipeline finished successfully.")
        return True

def convert_jsonl_to_markdown(output_dir):
    """
    Convert all JSONL files in the RESULTS_DIR into Markdown files.
    The Markdown files are saved under output_dir.
    """
    os.makedirs(output_dir, exist_ok=True)
    jsonl_files = glob.glob(os.path.join(RESULTS_DIR, "*.jsonl"))
    
    if not jsonl_files:
        print("No JSONL files found in", RESULTS_DIR)
        return
    
    for jsonl_file in jsonl_files:
        print(f"Processing {jsonl_file}...")
        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    doc = json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON in file {jsonl_file}: {e}")
                    continue
                
                # Get the source file name from metadata (or fallback to document id)
                metadata = doc.get("metadata", {})
                source_file = metadata.get("Source-File", doc.get("id", "unknown"))
                base_name = os.path.basename(source_file)
                name_without_ext, _ = os.path.splitext(base_name)
                markdown_filename = os.path.join(output_dir, f"{name_without_ext}.md")
                
                # Create Markdown content (header with source file name and OCR text)
                ocr_text = doc.get("text", "")
                markdown_content = f"# {base_name}\n\n" + ocr_text
                
                with open(markdown_filename, "w", encoding="utf-8") as md_file:
                    md_file.write(markdown_content)
                print(f"Created markdown: {markdown_filename}")

def process_directory(source_dir):
    """
    Process a single directory that may contain PDF files.
    This function clears the workspace, runs OCR on PDFs in source_dir,
    and then converts/moves the results into a corresponding destination folder.
    """
    # Get all PDF (or image) files in this directory (non-recursively)
    pdf_files = glob.glob(os.path.join(source_dir, "*.pdf"))
    # Optionally add jpg/png if your pipeline supports those
    pdf_files += glob.glob(os.path.join(source_dir, "*.png"))
    pdf_files += glob.glob(os.path.join(source_dir, "*.jpg"))
    pdf_files += glob.glob(os.path.join(source_dir, "*.jpeg"))
    
    if not pdf_files:
        print(f"No PDF/image files found in {source_dir}. Skipping.")
        return

    print(f"\nProcessing directory: {source_dir}")
    # Clear workspace completely before running this directory
    clear_workspace()
    
    # Run OCR pipeline on the pdf files
    if not run_ocr_pipeline(pdf_files):
        print(f"Error processing {source_dir}. Skipping conversion.")
        return

    # Determine the relative path from the base source directory.
    rel_path = os.path.relpath(source_dir, BASE_SOURCE_DIR)
    # Create a corresponding destination directory for markdown outputs
    dest_dir = os.path.join(BASE_DEST_DIR, rel_path)
    os.makedirs(dest_dir, exist_ok=True)
    
    # Convert the JSONL results to Markdown in the destination directory.
    convert_jsonl_to_markdown(dest_dir)
    
    # Optionally, move the JSONL files from the workspace to a backup location
    # (if you want to keep them separate, here we simply remove them after conversion).
    if os.path.exists(RESULTS_DIR):
        shutil.rmtree(RESULTS_DIR)
        os.makedirs(RESULTS_DIR, exist_ok=True)
        print(f"Moved (cleared) JSONL results for {source_dir}")

def main():
    """
    Walk through BASE_SOURCE_DIR recursively.
    For each directory that contains at least one PDF (or image) file,
    process it using the OCR pipeline and then convert the output to Markdown.
    """
    for root, dirs, files in os.walk(BASE_SOURCE_DIR):
        # Check if this directory contains any files with .pdf, .png, .jpg, or .jpeg extension.
        if any(file.lower().endswith((".pdf", ".png", ".jpg", ".jpeg")) for file in files):
            process_directory(root)
        else:
            print(f"Directory {root} does not contain PDF/image files. Skipping.")

if __name__ == "__main__":
    main()
