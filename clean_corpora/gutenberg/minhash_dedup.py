import hashlib
from pathlib import Path
from collections import defaultdict
import random
import re
from typing import List, Set, Dict, Tuple
import shutil
import os
from datetime import datetime
from tqdm import tqdm
import sys

class MinHashLSH:
    def __init__(self, num_perm: int = 100, threshold: float = 0.5, num_bands: int = 50):
        self.num_perm = num_perm
        self.threshold = threshold
        self.num_bands = num_bands
        self.rows_per_band = self.num_perm // self.num_bands
        self.hash_functions = self._generate_hash_functions()
        self.documents = {}
        self.lsh_buckets = defaultdict(list)
        
    def _generate_hash_functions(self) -> List[Tuple[int, int]]:
        random.seed(42)
        return [(random.randint(1, 2**32), random.randint(1, 2**32)) 
                for _ in range(self.num_perm)]
    
    def _minhash_signature(self, shingles: Set[str]) -> List[int]:
        signature = []
        for a, b in self.hash_functions:
            min_hash = float('inf')
            for shingle in shingles:
                hash_val = int(hashlib.md5(shingle.encode()).hexdigest(), 16)
                hash_code = (a * hash_val + b) % 2**32
                min_hash = min(min_hash, hash_code)
            signature.append(min_hash)
        return signature
    
    def _get_shingles(self, text: str, k: int = 5) -> Set[str]:
        text = re.sub(r'[^\w\s]', '', text.lower())
        text = ' '.join(text.split())
        return {text[i:i+k] for i in range(len(text) - k + 1)}
    
    def add_document(self, doc_id: str, content: str):
        shingles = self._get_shingles(content)
        signature = self._minhash_signature(shingles)
        self.documents[doc_id] = signature
        
        for band_idx in range(self.num_bands):
            start = band_idx * self.rows_per_band
            end = start + self.rows_per_band
            band = tuple(signature[start:end])
            bucket_id = (band_idx, hash(band))
            self.lsh_buckets[bucket_id].append(doc_id)
    
    def find_similar_pairs(self) -> Dict[str, List[Tuple[str, float]]]:
        similar_docs = defaultdict(list)
        seen_pairs = set()
        
        for bucket in self.lsh_buckets.values():
            for i in range(len(bucket)):
                for j in range(i + 1, len(bucket)):
                    doc1, doc2 = bucket[i], bucket[j]
                    if (doc1, doc2) not in seen_pairs:
                        seen_pairs.add((doc1, doc2))
                        seen_pairs.add((doc2, doc1))
                        
                        similarity = self._jaccard_similarity(
                            self.documents[doc1], 
                            self.documents[doc2]
                        )
                        
                        if similarity >= self.threshold:
                            similar_docs[doc1].append((doc2, similarity))
                            similar_docs[doc2].append((doc1, similarity))
        
        return similar_docs
    
    def _jaccard_similarity(self, sig1: List[int], sig2: List[int]) -> float:
        return sum(1 for x, y in zip(sig1, sig2) if x == y) / self.num_perm

class ProcessingLogger:
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.start_time = datetime.now()
        
        # Create log file and write header
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(f"Text Deduplication Process Log\nStarted at: {self.start_time}\n\n")
    
    def log(self, message: str, print_to_console: bool = True):
        """Log a message with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        
        if print_to_console:
            print(log_entry)
            
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')
    
    def log_error(self, message: str, error: Exception):
        """Log an error message with full exception details"""
        error_msg = f"ERROR: {message}\n"
        error_msg += f"Exception: {type(error).__name__}: {str(error)}"
        self.log(error_msg)
    
    def log_summary(self, stats: dict):
        """Log summary statistics"""
        duration = datetime.now() - self.start_time
        
        summary = "\n" + "="*50 + "\n"
        summary += "PROCESSING SUMMARY\n" + "="*50 + "\n"
        summary += f"Total duration: {duration}\n"
        
        for key, value in stats.items():
            summary += f"{key}: {value}\n"
            
        self.log(summary)

def organize_text_files(input_path: str, similarity_threshold: float = 0.5):
    """
    Organize text files by similarity, with detailed progress reporting
    """
    input_path = Path(input_path)
    
    # Create output directory
    output_base = input_path / "organized_texts"
    unique_texts = output_base / "unique"
    similar_texts = output_base / "similar"
    
    # Initialize logger
    log_file = input_path / f"deduplication_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    logger = ProcessingLogger(log_file)
    
    try:
        # Remove existing output directory if it exists
        if output_base.exists():
            logger.log(f"Cleaning existing output directory: {output_base}")
            shutil.rmtree(output_base)
        
        # Create directory structure
        logger.log("Creating directory structure...")
        unique_texts.mkdir(parents=True)
        similar_texts.mkdir(parents=True)
        
        # Initialize MinHash LSH
        lsh = MinHashLSH(threshold=similarity_threshold)
        
        # Get list of all text files
        txt_files = list(input_path.glob('*.txt'))
        total_files = len(txt_files)
        logger.log(f"Found {total_files} text files to process")
        
        # First pass: Load all documents into LSH
        logger.log("Phase 1: Processing files...")
        file_paths = {}  # Store original file paths
        
        with tqdm(total=total_files, desc="Processing files") as pbar:
            for file_path in txt_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    lsh.add_document(file_path.name, content)
                    file_paths[file_path.name] = file_path
                    pbar.update(1)
                except Exception as e:
                    logger.log_error(f"Error processing {file_path}", e)
        
        # Find similar documents
        logger.log("\nPhase 2: Finding similar documents...")
        similar_pairs = lsh.find_similar_pairs()
        
        # Create groups of similar documents
        groups = []
        processed = set()
        
        logger.log("Phase 3: Creating similarity groups...")
        for doc, similars in similar_pairs.items():
            if doc in processed:
                continue
                
            # Create new group
            group = {doc}
            processed.add(doc)
            
            # Add all similar documents to group
            for similar_doc, similarity in similars:
                if similar_doc not in processed:
                    group.add(similar_doc)
                    processed.add(similar_doc)
                    logger.log(f"Found similar files: '{doc}' and '{similar_doc}' "
                             f"(similarity: {similarity:.2%})", print_to_console=False)
            
            groups.append(group)
        
        # Copy files to appropriate locations
        logger.log("\nPhase 4: Organizing files...")
        
        # Handle groups of similar files
        similar_file_count = 0
        for i, group in enumerate(groups, 1):
            group_dir = similar_texts / f"similar_group_{i}"
            group_dir.mkdir()
            
            # Copy all files in the group
            for filename in group:
                src_path = file_paths[filename]
                dst_path = group_dir / filename
                shutil.copy2(src_path, dst_path)
                similar_file_count += 1
                logger.log(f"Copied similar file: {filename} -> similar_group_{i}", 
                          print_to_console=False)
        
        # Handle unique files (those not in any group)
        unique_files = set(file_paths.keys()) - processed
        unique_file_count = len(unique_files)
        
        for filename in unique_files:
            src_path = file_paths[filename]
            dst_path = unique_texts / filename
            shutil.copy2(src_path, dst_path)
            logger.log(f"Copied unique file: {filename} -> unique", print_to_console=False)
        
        # Log summary statistics
        stats = {
            "Total files processed": total_files,
            "Similar groups found": len(groups),
            "Files in similar groups": similar_file_count,
            "Unique files": unique_file_count,
            "Output directory": str(output_base),
            "Similarity threshold used": similarity_threshold
        }
        
        logger.log_summary(stats)
        
    except Exception as e:
        logger.log_error("Fatal error during processing", e)
        raise

if __name__ == "__main__":
    path = "/media/fivos/247968ad-2d9f-4d34-839a-ebc33dff1531/text_sources/gutenberg/"
    
    organize_text_files(path)