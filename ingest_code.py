import os
import shutil
import subprocess
import tarfile
import zipfile
import patoolib
import rarfile
from typing import List, Dict, Any
from config import ARCHIVE_EXTENSIONS, ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB, JAVA_DECOMPILER_CMD

class JavaClassDecompiler:
    """Decompiles Java bytecode (.class files) back to human-readable Java source (.java)."""
    
    def __init__(self, decompiler_cmd: str = JAVA_DECOMPILER_CMD):
        self.decompiler_cmd = decompiler_cmd

    def decompile_directory(self, target_dir: str) -> int:
        """Finds all .class files in target_dir and decompiles them into .java files."""
        decompiled_count = 0
        
        for root, _, files in os.walk(target_dir):
            for file in files:
                if file.endswith(".class") and not file.contains("$"):  # Skip inner anonymous classes
                    class_path = os.path.join(root, file)
                    java_output_path = os.path.splitext(class_path)[0] + ".java"
                    
                    # Only decompile if .java counterpart doesn't already exist
                    if not os.path.exists(java_output_path):
                        if self._decompile_single_file(class_path, root):
                            decompiled_count += 1
                            
        return decompiled_count

    def _decompile_single_file(self, class_file_path: str, output_dir: str) -> bool:
        """Invokes external decompiler CLI (CFR/Fernflower) or falls back to javap."""
        try:
            # Primary Attempt: CFR Decompiler
            cmd = [self.decompiler_cmd, class_file_path, "--outputdir", output_dir]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
            if result.returncode == 0:
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Fallback Attempt: Native JDK javap disassembler if CFR is not installed
        try:
            cmd = ["javap", "-c", "-p", class_file_path]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
            if result.returncode == 0 and result.stdout:
                java_path = os.path.splitext(class_file_path)[0] + ".java"
                with open(java_path, "w", encoding="utf-8") as f:
                    f.write(f"// Decompiled via javap fallback\n{result.stdout}")
                return True
        except Exception as e:
            print(f"[Decompile Error] Failed to decompile {class_file_path}: {e}")
            
        return False


class LargeCodebaseIngestor:
    """Extracts archives recursively (.rar, .zip, .jar, .war, .ear), decompiles bytecode, and catalogs."""
    
    def __init__(self, extract_dir: str = "./extracted_workspace"):
        self.extract_dir = extract_dir
        self.decompiler = JavaClassDecompiler()
        os.makedirs(self.extract_dir, exist_ok=True)

    def extract_archives(self, archive_paths: List[str]) -> str:
        """Initial pass to extract user-provided top-level archive files."""
        for path in archive_paths:
            filename = os.path.basename(path)
            target_subfolder = os.path.join(self.extract_dir, os.path.splitext(filename)[0])
            os.makedirs(target_subfolder, exist_ok=True)
            self._unpack_file(path, target_subfolder)
            
        # Perform nested extraction pass (e.g. .jar or .war inside .ear or .rar)
        self._extract_nested_archives_recursive(self.extract_dir)
        return self.extract_dir

    def _unpack_file(self, file_path: str, output_dir: str):
        """Unpacks individual archives based on format extension."""
        ext = os.path.splitext(file_path)[1].lower()
        try:
            if ext in [".zip", ".jar", ".war", ".ear"]:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(output_dir)
            elif ext == ".rar":
                rf = rarfile.RarFile(file_path)
                rf.extractall(output_dir)
            elif ext in [".tar", ".gz", ".tgz"]:
                with tarfile.open(file_path, 'r:*') as tar_ref:
                    tar_ref.extractall(output_dir)
            else:
                patoolib.extract_archive(file_path, outdir=output_dir)
        except Exception as e:
            print(f"[Extraction Warning] Skipping corrupted or protected file {file_path}: {e}")

    def _extract_nested_archives_recursive(self, directory: str, max_depth: int = 3):
        """Recursively scans and unpacks nested archives (.jar, .war, .ear) inside extracted code."""
        for depth in range(max_depth):
            found_nested = False
            for root, _, files in os.walk(directory):
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in ARCHIVE_EXTENSIONS:
                        full_path = os.path.join(root, file)
                        # Extract to folder named after the archive
                        unpack_dir = os.path.splitext(full_path)[0] + "_extracted"
                        if not os.path.exists(unpack_dir):
                            os.makedirs(unpack_dir, exist_ok=True)
                            self._unpack_file(full_path, unpack_dir)
                            found_nested = True
            if not found_nested:
                break

    def scan_and_catalog(self) -> Dict[str, Any]:
        """Decompiles remaining bytecode, scans directories, and builds a structured metadata index."""
        # Decompile any bytecode before indexing
        decompiled_count = self.decompiler.decompile_directory(self.extract_dir)

        catalog = {
            "presentation_layer": [],  # .jsp, .jspf, .tag, HTML
            "business_layer": [],      # .java (Beans, Servlets, EJBs)
            "config_layer": [],        # web.xml, ejb-jar.xml, properties
            "database_layer": []       # .sql scripts
        }

        total_files = 0
        total_size_bytes = 0

        for root, _, files in os.walk(self.extract_dir):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                full_path = os.path.join(root, file)
                
                if ext in ALLOWED_EXTENSIONS and ext != ".class":  # Ignore raw .class once decompiled
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
            "total_size_mb": round(total_size_bytes / (1024 * 1024), 2),
            "decompiled_classes": decompiled_count
        }
        return catalog

    def create_batches(self, file_list: List[Dict[str, Any]], batch_size: int = 15) -> List[List[Dict[str, Any]]]:
        """Splits file catalog into manageable batches for OpenRouter agents."""
        return [file_list[i:i + batch_size] for i in range(0, len(file_list), batch_size)]
