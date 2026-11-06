# Retrieval & Citation Rules

## Citation Isolation Protocol
* Every retrieved chunk is sanitized into `[S1] <Filename> Page <N>` before model presentation.
* Raw filesystem paths, document IDs, and hashes are decoupled into an internal memory registry.
* Answers provide exact citations via `[[src:Sn]]`.

## Dynamic Relative Threshold
* Let $S_{max}$ be the top similarity score in the candidate set.
* Chunks with score $S < S_{max} 	imes 0.9$ are dynamically pruned.
