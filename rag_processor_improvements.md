# RAG Processor Chunking Improvements

## Issues Found

### 1. Chunk Size Issues
- Some chunks are too small (< 300 tokens) - e.g., chunk 1 with only 12 tokens
- Token estimation is rough (len(text) // 4) which may cause inaccurate sizing
- Target size of 1000 is acceptable but could be optimized

### 2. Poor Boundaries
- Chunks break mid-content without preserving context
- Mixed content types (code, diagrams, text) in single chunks
- No semantic awareness when splitting large sections

### 3. Context Loss
- Minimal overlap (100 tokens) may not preserve enough context
- Headers/titles repeated without sufficient context

## Recommended Changes

### 1. Improve Token Counting
Replace the rough estimation with a more accurate method:

```python
import tiktoken  # OpenAI's tokenizer

def estimate_tokens(self, text):
    """More accurate token counting using tiktoken"""
    try:
        # Use cl100k_base encoding (GPT-4 compatible)
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except:
        # Fallback to rough estimation if tiktoken not available
        # Better estimation: ~0.75 words per token, ~5 chars per word
        return len(text) // 3.75
```

### 2. Adjust Chunk Size Parameters
```python
# Optimal chunking configuration
self.CHUNK_SIZE_MIN = 500      # Increased from 300
self.CHUNK_SIZE_TARGET = 800   # Decreased from 1000 for better coherence
self.CHUNK_SIZE_MAX = 1200     # Decreased from 1500
self.CHUNK_OVERLAP = 150       # Increased from 100 for better context
```

### 3. Implement Semantic Chunking
Add logic to respect content boundaries:

```python
def create_chunks(self, content, metadata, base_title=""):
    """Split content into logical chunks preserving context"""
    chunks = []
    sections = self.extract_sections(content)
    
    if not sections:
        return chunks
    
    # Group related sections together
    semantic_groups = self._group_related_sections(sections)
    
    for group in semantic_groups:
        group_tokens = sum(self.estimate_tokens(s['content']) for s in group)
        
        # If group is within limits, keep together
        if self.CHUNK_SIZE_MIN <= group_tokens <= self.CHUNK_SIZE_MAX:
            chunks.append(self._create_chunk_from_sections(group, metadata))
        # If too large, split intelligently
        elif group_tokens > self.CHUNK_SIZE_MAX:
            chunks.extend(self._split_large_group(group, metadata))
        # If too small, try to merge with adjacent groups
        else:
            # Implementation for merging small groups
            pass
    
    return chunks

def _group_related_sections(self, sections):
    """Group sections by semantic similarity"""
    groups = []
    current_group = []
    
    for i, section in enumerate(sections):
        # Check if this section should start a new group
        if self._is_major_boundary(section, sections[i-1] if i > 0 else None):
            if current_group:
                groups.append(current_group)
            current_group = [section]
        else:
            current_group.append(section)
    
    if current_group:
        groups.append(current_group)
    
    return groups

def _is_major_boundary(self, current_section, previous_section):
    """Detect major content boundaries"""
    # New H1 or H2 usually indicates major boundary
    if current_section['level'] <= 2:
        return True
    
    # Check for content type changes (code -> text, etc)
    if previous_section:
        prev_has_code = '```' in previous_section['content']
        curr_has_code = '```' in current_section['content']
        if prev_has_code != curr_has_code:
            return True
    
    return False
```

### 4. Preserve Code Block Integrity
```python
def _split_large_group(self, group, metadata):
    """Split large groups while preserving code blocks"""
    chunks = []
    current_chunk_content = ""
    current_chunk_sections = []
    current_tokens = 0
    
    for section in group:
        # Never split code blocks
        if '```' in section['content']:
            code_blocks = self._extract_code_blocks(section['content'])
            for block in code_blocks:
                if current_tokens + block['tokens'] > self.CHUNK_SIZE_MAX:
                    # Save current chunk
                    if current_chunk_content:
                        chunks.append(self._finalize_chunk(
                            current_chunk_content, 
                            current_chunk_sections, 
                            current_tokens, 
                            metadata
                        ))
                    # Start new chunk with this code block
                    current_chunk_content = block['content']
                    current_chunk_sections = [section['title']]
                    current_tokens = block['tokens']
                else:
                    current_chunk_content += "\n\n" + block['content']
                    current_tokens += block['tokens']
        else:
            # Regular text - can be split by paragraphs
            # ... existing paragraph splitting logic ...
```

### 5. Add Chunk Quality Validation
```python
def _validate_chunk(self, chunk):
    """Ensure chunk meets quality standards"""
    content = chunk['content']
    tokens = chunk['token_count']
    
    # Check size constraints
    if tokens < self.CHUNK_SIZE_MIN:
        return False, "Chunk too small"
    
    if tokens > self.CHUNK_SIZE_MAX:
        return False, "Chunk too large"
    
    # Check for incomplete code blocks
    if content.count('```') % 2 != 0:
        return False, "Incomplete code block"
    
    # Check for orphaned content
    if content.strip().startswith(('else:', 'elif:', '}')):
        return False, "Chunk starts with orphaned code"
    
    return True, "Valid"
```

## Implementation Priority

1. **High Priority**: Fix token counting and adjust size parameters
2. **Medium Priority**: Implement semantic boundary detection
3. **Low Priority**: Add validation and quality checks

These improvements will result in:
- More consistent chunk sizes (500-1200 tokens)
- Better semantic coherence within chunks
- Preserved code block integrity
- Improved context retention for RAG retrieval