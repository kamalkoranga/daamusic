# DSA Concepts Used in daamusic

| DSA Concept         | Where in Code                          | Purpose                                      |
|---------------------|----------------------------------------|----------------------------------------------|
| Custom Data Structure | `OfflineSong` class                    | Encapsulate song data                        |
| DFS                 | `scan_music_folder`                    | Traverse directories for music files         |
| Insertion Sort      | `insertion_sort_by_size`               | Sort songs by file size                      |
| Heap/Priority Queue | `heapq.nlargest` in `play_offline_music`| Find top 3 largest files                     |
| Linear Search       | `linear_search_title`                  | Search by keyword in song titles             |
| Binary Search       | `binary_search_title`                  | Search by exact title                        |
| Table Display       | Table with `[Top 3 Largest]` mark      | Show DSA results to user                     |