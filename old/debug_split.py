import os

file_path = 'need_trans_txt/關於白羊座.txt'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

print(f"Total length: {len(text)}")
print(f"First 200 chars repr: {repr(text[:200])}")

paragraphs_double_newline = text.split('\n\n')
print(f"\nSplit by \\n\\n count: {len(paragraphs_double_newline)}")
for i, p in enumerate(paragraphs_double_newline[:3]):
    print(f"  Para {i} length: {len(p)}")

paragraphs_newline = text.split('\n')
print(f"\nSplit by \\n count: {len(paragraphs_newline)}")

# Simulate the current split logic
chunks = []
current_chunk = []
current_length = 0
max_size = 2000

print(f"\nSimulating split with max_size={max_size}...")
paras = paragraphs_double_newline # This is what trans.py uses

for para in paras:
    if current_length + len(para) > max_size and current_chunk:
        chunks.append(current_length)
        current_chunk = []
        current_length = 0
    
    current_chunk.append(para)
    current_length += len(para) + 2

if current_chunk:
    chunks.append(current_length)

print(f"Simulated chunks count: {len(chunks)}")
print(f"Chunk sizes: {chunks}")
