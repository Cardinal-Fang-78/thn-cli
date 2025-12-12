\# PDF Exports



This directory contains generated PDF documentation using the THN PDF pipeline.



PDFs include:



\- THN Versioning Policy  

\- Tenant documentation  

\- Sync V2 delta reports  

\- Release notes  

\- Negotiation visualizations (when exported as PDF)



To regenerate all PDFs:



```

python tools/generate\_policy\_pdf.py

python tools/release\_pdf.py

```



All PDFs use THN-standard dark backgrounds (#444444) with light text.



