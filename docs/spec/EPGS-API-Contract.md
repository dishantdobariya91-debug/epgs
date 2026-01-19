\# EPGS API Contract



\## POST /run



\### Input

\- scenario\_path (string)

\- output\_root (optional string)



\### Output (guaranteed)

\- run\_id

\- permission

\- stop\_issued

\- terminal\_stop

\- final\_state

\- execution\_hash

\- ledger\_dir



\## POST /verify



\### Input

\- ledger\_dir (preferred)

\- output\_root (fallback)



\### Output

\- ok (boolean)

\- count (int)

\- final\_hash (string)

\- reason (string, if failed)



