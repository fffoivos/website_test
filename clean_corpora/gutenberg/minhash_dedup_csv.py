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
import csv

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

def deduplicate_texts(input_path: str, similarity_threshold: float = 0.95):
    """
    Deduplicate text files by similarity and generate a CSV report of relationships
    """
    input_path = Path(input_path)
    
    # Create output directory
    output_base = input_path / "deduplicated_texts"
    unique_texts = output_base / "unique"
    
    # Create log file
    log_file = input_path / f"deduplication_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"Text Deduplication Log\nStarted at: {datetime.now()}\n\n")
    
    # Remove existing output directory if it exists
    if output_base.exists():
        shutil.rmtree(output_base)
    
    # Create directory structure
    unique_texts.mkdir(parents=True)
    
    # Initialize MinHash LSH
    lsh = MinHashLSH(threshold=similarity_threshold)
    
    # Get list of all text files
    txt_files = list(input_path.glob('*.txt'))
    total_files = len(txt_files)
    print(f"Found {total_files} text files to process")
    
    # Process all files
    file_paths = {}
    with tqdm(total=total_files, desc="Processing files") as pbar:
        for file_path in txt_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                lsh.add_document(file_path.name, content)
                file_paths[file_path.name] = file_path
                pbar.update(1)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
    
    # Find similar documents
    print("\nFinding similar documents...")
    similar_pairs = lsh.find_similar_pairs()
    
    # Create groups and identify representative documents
    groups = []
    processed = set()
    representative_docs = {}  # Maps group representative to list of similar docs
    
    print("Creating similarity groups...")
    for doc, similars in similar_pairs.items():
        if doc in processed:
            continue
        
        # Create new group
        group = {doc}
        processed.add(doc)
        
        # Add all similar documents to group
        similar_list = []
        for similar_doc, similarity in similars:
            if similar_doc not in processed:
                group.add(similar_doc)
                processed.add(similar_doc)
                similar_list.append((similar_doc, similarity))
        
        # Use the first document as representative
        representative_docs[doc] = similar_list
        groups.append(group)
    
    # Identify unique documents (those not in any group)
    unique_files = set(file_paths.keys()) - processed
    
    # Copy representative and unique files to output directory
    print("\nCopying deduplicated files...")
    all_representatives = []
    
    # Copy group representatives
    for doc in representative_docs.keys():
        src_path = file_paths[doc]
        dst_path = unique_texts / doc
        shutil.copy2(src_path, dst_path)
        all_representatives.append(doc)
    
    # Copy unique files
    for doc in unique_files:
        src_path = file_paths[doc]
        dst_path = unique_texts / doc
        shutil.copy2(src_path, dst_path)
        all_representatives.append(doc)
    
    # Generate CSV report
    csv_path = output_base / "similarity_report.csv"
    max_similars = max(len(similars) for similars in representative_docs.values()) if representative_docs else 0
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Create header row
        header = ['Unique_File'] + [f'{i+1}_Similar (Similarity %)' for i in range(max_similars)]
        writer.writerow(header)
        
        # Write rows for files with similar documents
        for doc in all_representatives:
            row = [doc]
            if doc in representative_docs:
                similars = representative_docs[doc]
                # Add similar documents with similarity scores
                for similar_doc, similarity in similars:
                    row.append(f"{similar_doc} ({similarity:.1%})")
                # Pad with empty strings if needed
                row.extend([''] * (max_similars - len(similars)))
            else:
                # Add empty strings for files with no similar documents
                row.extend([''] * max_similars)
            writer.writerow(row)
    
    # Print summary
    print("\nDeduplication complete!")
    print(f"Total files processed: {total_files}")
    print(f"Unique files: {len(all_representatives)}")
    print(f"Similar groups found: {len(groups)}")
    print(f"Output directory: {output_base}")
    print(f"Similarity report: {csv_path}")

if __name__ == "__main__":
    path = "/home/fivos/Desktop/test"
    deduplicate_texts(path)