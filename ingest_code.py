import os
import shutil
import patoolib
import rarfile
import zipfile
from typing import List, Dict, Any
from config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB

class LargeCodebaseIngestor:
    def __init__(self, extract_dir: str = "./extracted_workspace"):
        self.extract_dir = extract_dir
        os.makedirs(self.extract_dir, exist_ok=True)

    def extract_archives(self, archive_paths: List[str]) -> str:
        """Extracts .rar, .zip, and archive files recursively into workspace."""
        for path in archive_paths:
            filename = os.path.basename(path)
            target_subfolder = os.path.join(self.extract_dir, os.path.splitext(filename))
            os.makedirs(target_subfolder, exist_ok=True)
            
            try:
                if path.endswith('.rar'):
                    rf = rarfile.RarFile(path)
                    rf.extractall(target_subfolder)
                elif path.endswith('.zip'):
                    with zipfile.ZipFile(path, 'r') as zip_ref:
                        zip_ref.extractall(target_subfolder)
                else:
                    patoolib.extract_archive(path, outdir=target_subfolder)
            except Exception as e:
                print(f"[Warning] Failed extracting {path}: {str(e)}")
                
        return self.extract_dir

    def scan_and_catalog(self) -> Dict[str, Any]:
        """Scans extracted code, filters out binaries/jars, and builds a modular catalog."""
        catalog = {
            "presentation_layer": [],  # .jsp, .jspf, .tag
            "business_layer": [],      # .java (Beans, Servlets, Services)
            "config_layer": [],        # web.xml, context.xml, properties
            "database_layer": []       # SQL scripts, DAOs
        }

        total_files = 0
        total_size_bytes = 0

        for root, _, files in os.walk(self.extract_dir):
            for file in files:
                ext = os.path.splitext(file)[4].lower()
                full_path = os.path.join(root, file)
                
                # Filter by extension and file size
                if ext in ALLOWED_EXTENSIONS:
                    file_size = os.path.getsize(full_path)
                    if file_size <= MAX_FILE_SIZE_MB * 1024 * 1024:
                        total_files += 1
                        total_size_bytes += file_size
                        
                        relative_path = os.path.relpath(full_path, self.extract_dir)
                        item = {"path": full_path, "relative_path": relative_path, "size": file_size}

                        if ext in ['.jsp', '.jspf', '.tag', '.html']:
                            catalog["presentation_layer"].append(item)
                        elif ext in ['.java']:
                            catalog["business_layer"].append(item)
                        elif ext in ['.xml', '.properties', '.tld']:
                            catalog["config_layer"].append(item)
                        elif ext in ['.sql']:
                            catalog["database_layer"].append(item)

        catalog["stats"] = {
            "total_files": total_files,
            "total_size_mb": round(total_size_bytes / (1024 * 1024), 2)
        }
        return catalog

    def create_batches(self, file_list: List[Dict[str, Any]], batch_size: int = 15) -> List[List[Dict[str, Any]]]:
        """Splits file catalog into manageable batches for OpenRouter agents."""
        return [file_list[i:i + batch_size] for i in range(0, len(file_list), batch_size)]
