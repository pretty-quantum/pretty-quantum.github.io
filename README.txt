Pretty Quantum — GitHub Pages ready package

Upload these files to the TOP LEVEL of your GitHub Pages repository:

    index.html
    style.css
    publications.html
    publications.css
    ikuta.bib

Important:
- style.css is the common site design used by the homepage.
- publications.css contains ONLY publication-page-specific formatting.
- Uploading publications.css will therefore not overwrite the homepage design.
- publications.html loads both style.css and publications.css.
- Publication numbering restarts at 1 for each year.
- Duplicate arXiv records are omitted when a journal publication with the same title exists.
- Journal + volume + page/article number is the clickable DOI/link.
- The year is outside the link.

GitHub upload:
1. Open your USERNAME.github.io repository.
2. Add file -> Upload files.
3. Drag the files above into the upload area.
4. Commit changes.
5. Open:
       https://USERNAME.github.io/
   and:
       https://USERNAME.github.io/publications.html

Note:
Profile / Conference / Guide / Qjapanimation pages are not included yet.
Links to those pages will work after corresponding HTML files are added.
