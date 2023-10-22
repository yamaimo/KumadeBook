module.exports = {
  title: 'タスクランナーkumade - Pythonで作業を自動化しよう',
  author: 'やまいも <hello@yamaimo.dev>',
  size: 'A5',
  theme: '@vivliostyle/theme-techbook@^1.0.0',
  entry: [
    'cover1.md',
    'opening.md',
    'toc.md',
    'chap1_intro.md',
    'chap2_getstart.md',
    'chap3_kumadefile.md',
    'chap4_usecase.md',
    'closing.md',
    'cover4.md',
  ],
  output: [
    './KumadeBook.pdf',
  ],
}
