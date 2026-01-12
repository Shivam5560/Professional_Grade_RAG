# BM25 Hybrid Search Issues & Solutions
## Analysis of langchain4j Implementation Problems

---

## 🔴 Problem Summary

Your friend's langchain4j implementation is experiencing severe quality degradation after introducing BM25 + Reranking, despite the correct approach being used in the Python implementation shown in this project.

### Initial State (Problem #1)
- **Issue**: BM25 sending entire files (term frequency index, document length index, chunk index) into LLM context
- **Result**: 100k+ tokens, accurate but extremely expensive
- **Root Cause**: BM25 index files being passed as context instead of retrieved chunks

### Current State (Problem #2)
- **Configuration**: 
  - Top 10 from pgvector
  - Top 10 from BM25  
  - Merge to 20 → Rerank to 10
  - 3 API calls for 3 prompt subsets
  - ~9k tokens total
- **Result**: Much worse quality than original 40 segments without BM25
- **Root Cause**: Multiple issues (detailed below)

---

## 🔍 Core Problems Identified

### 1. **Insufficient Context Window**
```
Before: 40 segments
Now: 10 segments (after reranking)
Loss: 75% reduction in context
```

**Why This Matters:**
- RAG systems need sufficient context diversity
- 10 segments may miss critical information spread across multiple chunks
- The "40 segments" baseline was working because it provided enough coverage

### 2. **Incorrect BM25 Implementation**
Based on the Python implementation, BM25 should:
- ✅ Index individual **chunks/segments** (not entire files)
- ✅ Return **scored segments** (not index files)
- ✅ Work at the same granularity as vector search

**What's Likely Happening in langchain4j:**
```java
// ❌ WRONG: Returning BM25 index files as context
BM25Index.getIndexFiles() → [term_freq.txt, doc_length.txt, chunks.txt]

// ✅ CORRECT: Should return scored segments
BM25Index.search(query, topK=10) → [Segment1, Segment2, ...]
```

### 3. **RRF (Reciprocal Rank Fusion) Misconfiguration**
The Python implementation uses **score normalization + weighted combination**, not pure RRF:

```python
# Current Python approach (retriever.py)
def _normalize_scores(self, nodes: List[NodeWithScore]) -> List[NodeWithScore]:
    scores = [n.score for n in nodes]
    if not scores:
        return nodes
    
    min_score, max_score = min(scores), max(scores)
    if max_score == min_score:
        normalized = [1.0] * len(nodes)
    else:
        normalized = [(s - min_score) / (max_score - min_score) for s in scores]
    
    return [
        NodeWithScore(node=n.node, score=norm_score)
        for n, norm_score in zip(nodes, normalized)
    ]

# Weighted fusion
combined_score = (alpha * bm25_score) + ((1 - alpha) * vector_score)
```

**RRF Formula (if using pure RRF):**
```
RRF_score = Σ(1 / (k + rank_i))
where k = 60 (typical constant), rank_i = rank in each retriever
```

### 4. **3 Separate API Calls = Context Fragmentation**
```
Call 1: 10 segments for prompt subset 1
Call 2: 10 segments for prompt subset 2  
Call 3: 10 segments for prompt subset 3
Total: 30 segment references (but only 10 unique per call)
```

**Issues:**
- Each call sees different context windows
- No cross-prompt context sharing
- Reranking happens 3 times independently
- Total tokens ~9k but fragmented across calls

---

## ✅ Solutions & Best Practices

### Solution 1: Increase Top-K Values

Based on your successful "40 segments" baseline:

```java
// Recommended configuration
int VECTOR_TOP_K = 30;  // Increased from 10
int BM25_TOP_K = 30;    // Increased from 10
int MERGED_TOP_K = 40;  // Before reranking
int FINAL_TOP_K = 20;   // After reranking (not 10)

// Pipeline
pgvector.search(query, VECTOR_TOP_K)  → 30 segments
bm25.search(query, BM25_TOP_K)         → 30 segments
merge() → deduplicate                  → ~40-50 unique segments
rerank()                               → 20 segments
```

### Solution 2: Fix BM25 Implementation

**Correct langchain4j BM25 Usage:**

```java
// ❌ WRONG
List<String> bm25Results = bm25Index.getIndexFiles();

// ✅ CORRECT
import dev.langchain4j.store.embedding.bm25.BM25EmbeddingStore;
import dev.langchain4j.data.segment.TextSegment;

// Initialize BM25 with segments (not files)
BM25EmbeddingStore bm25Store = new BM25EmbeddingStore();

// Add segments during indexing
for (TextSegment segment : documentSegments) {
    bm25Store.add(segment);
}

// Search returns segments (not index files)
List<EmbeddingMatch<TextSegment>> bm25Results = 
    bm25Store.search(query, BM25_TOP_K);
```

**Note:** langchain4j does NOT have built-in BM25 by default. You need to:
1. Use a library like `org.apache.lucene:lucene-core` for BM25
2. Or use `dev.langchain4j.retriever.bm25` if available (check version)
3. Or implement custom BM25 using the Python logic

### Solution 3: Implement Proper Hybrid Retrieval

```java
public class HybridRetriever {
    
    private final VectorStore pgVector;
    private final BM25Store bm25;
    private final Reranker reranker;
    
    public List<TextSegment> retrieve(String query, int finalTopK) {
        // Step 1: Parallel retrieval
        List<ScoredSegment> vectorResults = pgVector.search(query, 30);
        List<ScoredSegment> bm25Results = bm25.search(query, 30);
        
        // Step 2: Normalize scores (CRITICAL)
        vectorResults = normalizeScores(vectorResults);
        bm25Results = normalizeScores(bm25Results);
        
        // Step 3: Merge with weighted fusion
        double alpha = 0.5; // 50-50 weight
        Map<String, ScoredSegment> merged = new HashMap<>();
        
        for (ScoredSegment seg : vectorResults) {
            merged.put(seg.id, new ScoredSegment(seg.segment, alpha * seg.score));
        }
        
        for (ScoredSegment seg : bm25Results) {
            if (merged.containsKey(seg.id)) {
                // Combine scores
                double newScore = merged.get(seg.id).score + ((1 - alpha) * seg.score);
                merged.put(seg.id, new ScoredSegment(seg.segment, newScore));
            } else {
                merged.put(seg.id, new ScoredSegment(seg.segment, (1 - alpha) * seg.score));
            }
        }
        
        // Step 4: Sort and take top candidates for reranking
        List<ScoredSegment> topCandidates = merged.values().stream()
            .sorted((a, b) -> Double.compare(b.score, a.score))
            .limit(40)  // More candidates for reranker
            .collect(Collectors.toList());
        
        // Step 5: Rerank
        List<TextSegment> reranked = reranker.rerank(query, topCandidates);
        
        // Step 6: Return final top-k
        return reranked.subList(0, Math.min(finalTopK, reranked.size()));
    }
    
    private List<ScoredSegment> normalizeScores(List<ScoredSegment> segments) {
        if (segments.isEmpty()) return segments;
        
        double min = segments.stream().mapToDouble(s -> s.score).min().orElse(0);
        double max = segments.stream().mapToDouble(s -> s.score).max().orElse(1);
        
        if (max == min) return segments;
        
        return segments.stream()
            .map(s -> new ScoredSegment(
                s.segment, 
                (s.score - min) / (max - min)
            ))
            .collect(Collectors.toList());
    }
}
```

### Solution 4: Unified Context Across API Calls

Instead of 3 separate retrievals:

```java
// ❌ WRONG: Fragmented context
for (String promptSubset : promptSubsets) {
    List<Segment> context = retrieve(promptSubset, 10); // Different for each
    callLLM(promptSubset, context);
}

// ✅ BETTER: Shared context with prompt-specific reranking
List<Segment> baseContext = retrieve(mainQuery, 40); // Large shared pool

for (String promptSubset : promptSubsets) {
    // Rerank shared context based on prompt subset
    List<Segment> promptContext = reranker.rerank(promptSubset, baseContext)
        .subList(0, 15);  // Top 15 for this specific prompt
    
    callLLM(promptSubset, promptContext);
}
```

---

## 📊 Recommended Configuration

### Conservative Approach (Balanced Quality & Cost)
```
Vector Search:     Top 25
BM25 Search:       Top 25  
Merged Candidates: ~35-40 unique
After Reranking:   Top 15-20 per prompt
API Calls:         3 calls × 15 segments = ~12k tokens
```

### Aggressive Approach (Maximum Quality)
```
Vector Search:     Top 40
BM25 Search:       Top 40
Merged Candidates: ~50-60 unique
After Reranking:   Top 25-30 per prompt
API Calls:         3 calls × 25 segments = ~18k tokens
```

### Token Budget Optimization
```java
// Adaptive top-k based on query complexity
int topK = queryComplexityScore > 0.7 ? 25 : 15;

// Deduplication across prompts
Set<String> usedSegments = new HashSet<>();
for (String prompt : prompts) {
    List<Segment> context = getTopK(prompt, 20)
        .stream()
        .filter(seg -> !usedSegments.contains(seg.id))
        .limit(15)
        .collect(Collectors.toList());
    
    usedSegments.addAll(context.stream().map(s -> s.id).collect(Collectors.toSet()));
}
```

---

## 🔧 langchain4j Compatibility Check

### Built-in Support Status

| Feature | langchain4j Support | Implementation |
|---------|-------------------|----------------|
| Vector Search | ✅ Built-in | `EmbeddingStore` interface |
| BM25 Search | ⚠️ Limited | Need Lucene or custom impl |
| Reranking | ✅ Built-in | `Reranker` interface |
| RRF Fusion | ❌ Not built-in | Manual implementation required |
| Score Normalization | ❌ Not built-in | Manual implementation required |

### Dependencies Needed

```xml
<!-- pom.xml -->
<dependencies>
    <!-- langchain4j core -->
    <dependency>
        <groupId>dev.langchain4j</groupId>
        <artifactId>langchain4j</artifactId>
        <version>0.35.0</version>
    </dependency>
    
    <!-- PGVector support -->
    <dependency>
        <groupId>dev.langchain4j</groupId>
        <artifactId>langchain4j-embeddings-store-pgvector</artifactId>
        <version>0.35.0</version>
    </dependency>
    
    <!-- BM25 via Lucene -->
    <dependency>
        <groupId>org.apache.lucene</groupId>
        <artifactId>lucene-core</artifactId>
        <version>9.9.1</version>
    </dependency>
    
    <dependency>
        <groupId>org.apache.lucene</groupId>
        <artifactId>lucene-queryparser</artifactId>
        <version>9.9.1</version>
    </dependency>
</dependencies>
```

### Custom BM25 Implementation for langchain4j

```java
import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.document.*;
import org.apache.lucene.index.*;
import org.apache.lucene.search.*;
import org.apache.lucene.store.ByteBuffersDirectory;

public class LuceneBM25Store {
    
    private final ByteBuffersDirectory directory;
    private final StandardAnalyzer analyzer;
    private IndexWriter writer;
    private DirectoryReader reader;
    private IndexSearcher searcher;
    
    public LuceneBM25Store() throws IOException {
        this.directory = new ByteBuffersDirectory();
        this.analyzer = new StandardAnalyzer();
        
        IndexWriterConfig config = new IndexWriterConfig(analyzer);
        config.setSimilarity(new BM25Similarity()); // Use BM25 scoring
        this.writer = new IndexWriter(directory, config);
    }
    
    public void add(String id, String content, Map<String, String> metadata) 
            throws IOException {
        Document doc = new Document();
        doc.add(new StringField("id", id, Field.Store.YES));
        doc.add(new TextField("content", content, Field.Store.YES));
        
        for (Map.Entry<String, String> entry : metadata.entrySet()) {
            doc.add(new StringField(entry.getKey(), entry.getValue(), Field.Store.YES));
        }
        
        writer.addDocument(doc);
    }
    
    public void commit() throws IOException {
        writer.commit();
        if (reader != null) {
            reader.close();
        }
        reader = DirectoryReader.open(directory);
        searcher = new IndexSearcher(reader);
        searcher.setSimilarity(new BM25Similarity()); // Use BM25 for search
    }
    
    public List<ScoredSegment> search(String query, int topK) throws Exception {
        if (searcher == null) {
            commit();
        }
        
        QueryParser parser = new QueryParser("content", analyzer);
        Query luceneQuery = parser.parse(QueryParser.escape(query));
        
        TopDocs topDocs = searcher.search(luceneQuery, topK);
        List<ScoredSegment> results = new ArrayList<>();
        
        for (ScoreDoc scoreDoc : topDocs.scoreDocs) {
            Document doc = searcher.doc(scoreDoc.doc);
            results.add(new ScoredSegment(
                doc.get("id"),
                doc.get("content"),
                scoreDoc.score
            ));
        }
        
        return results;
    }
}
```

---

## 🎯 Action Plan for Your Friend

### Phase 1: Immediate Fixes (1-2 days)
1. ✅ **Verify BM25 returns segments, not index files**
   - Debug and log what BM25 is actually returning
   - If returning files → Fix implementation using Lucene

2. ✅ **Increase top-k values**
   - Change to: 30 vector + 30 BM25 → 40 merged → 20 reranked
   - Test quality improvement

3. ✅ **Add score normalization**
   - Implement `normalizeScores()` method from Solution 3
   - Essential for fair fusion

### Phase 2: Optimization (3-5 days)
4. ✅ **Implement proper hybrid retrieval**
   - Use weighted score fusion (alpha = 0.5 as starting point)
   - Merge duplicate segments by ID

5. ✅ **Optimize context sharing**
   - Retrieve once, rerank 3 times for different prompts
   - Reduces token waste

### Phase 3: Testing & Tuning (Ongoing)
6. ✅ **A/B test configurations**
   ```
   Test 1: 40 segments baseline (no BM25) - Quality reference
   Test 2: 20-30 hybrid segments - Find sweet spot
   Test 3: Adjust alpha weight (0.3, 0.5, 0.7)
   ```

7. ✅ **Monitor metrics**
   - Answer accuracy
   - Token usage
   - Latency
   - BM25 vs Vector contribution (which sources are used more)

---

## 🚨 Critical Checklist

- [ ] BM25 returns **segments** not **index files**
- [ ] BM25 search works at **same granularity** as vector search
- [ ] Score normalization applied **before** fusion
- [ ] Using **at least 20 final segments** (not 10)
- [ ] Reranker receives **40+ candidates** (not 20)
- [ ] langchain4j version supports required features or custom implementation added
- [ ] Testing shows quality **comparable or better** than 40-segment baseline

---

## 📚 References

### Python Implementation (This Project)
- [bm25_service.py](backend/app/services/bm25_service.py) - BM25 indexing & search
- [retriever.py](backend/app/core/retriever.py) - Hybrid retrieval with fusion
- [reranker.py](backend/app/core/reranker.py) - Reranking logic

### langchain4j Resources
- Official Docs: https://docs.langchain4j.dev/
- Retrieval Guide: https://docs.langchain4j.dev/tutorials/rag
- BM25 Discussion: https://github.com/langchain4j/langchain4j/discussions

### BM25 Theory
- Okapi BM25: https://en.wikipedia.org/wiki/Okapi_BM25
- Lucene BM25Similarity: https://lucene.apache.org/core/9_9_1/core/org/apache/lucene/search/similarities/BM25Similarity.html

---

## 💡 Key Takeaway

The issue is NOT with the approach (hybrid retrieval + reranking is correct), but with:
1. **Implementation details** (BM25 returning wrong data)
2. **Configuration values** (too few segments in final context)
3. **Missing normalization** (unfair score fusion)

Fix these three, and quality should match or exceed the 40-segment baseline while keeping tokens under control (~12-15k instead of 100k).
