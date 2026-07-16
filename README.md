# Lexical Analyzer Simulator

A web-based **Lexical Analyzer Simulator** developed using **Python** and **Flask** that demonstrates fundamental concepts of **Compiler Design** and **Theory of Automata**. The application performs lexical analysis on source code and visualizes the transformation of Regular Expressions into ε-NFA, NFA, DFA, and Minimized DFA.

🌐 **Live Demo:** https://lexical-analyzer-simulator.onrender.com

💻 **GitHub Repository:** https://github.com/rgilani18/Lexical-Analyzer-Simulator

---

## Project Overview

The Lexical Analyzer Simulator is an educational web application designed to help students understand the working of lexical analyzers and finite automata.

Users can enter source code, perform lexical analysis, generate tokens, and visualize automata generated from Regular Expressions using standard compiler algorithms.

This project was developed as a **group project** for the **Theory of Automata** course.

---

## Features

- Lexical Analysis (Token Generation)
- Regular Expression Processing
- Thompson's Construction (Regex → ε-NFA)
- ε-NFA → NFA Conversion
- NFA → DFA Conversion (Subset Construction)
- DFA Minimization
- Interactive Visualization of Automata
- Sample Input Programs
- Error Detection for Invalid Tokens

---

## Algorithms Implemented

- Thompson's Construction
- ε-Closure Algorithm
- Subset Construction
- DFA Minimization
- Tokenization

---

## Technologies Used

- Python
- Flask
- HTML5
- CSS3
- JavaScript

---

## Project Structure

```
Lexical-Analyzer-Simulator/
│
├── templates/
│   ├── home.html
│   ├── index.html
│   ├── visual.html
│   ├── visual_enfa.html
│   └── visual_nfa.html
│
├── screenshots/
│
├── app.py
├── automata.py
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Installation

Clone the repository

```bash
git clone https://github.com/rgilani18/Lexical-Analyzer-Simulator.git
```

Move into the project directory

```bash
cd Lexical-Analyzer-Simulator
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run the application

```bash
python app.py
```

Open your browser

```
http://localhost:5050
```

---

## Screenshots

### Home Page

<img width="948" height="441" alt="image" src="https://github.com/user-attachments/assets/e6362e88-2981-44d3-88d4-afae9765c481" />

---

### Lexical Analysis

<img width="959" height="430" alt="image" src="https://github.com/user-attachments/assets/d12cd627-8453-4db4-9227-52c62c86c84a" />


---

### ε-NFA
<img width="950" height="425" alt="image" src="https://github.com/user-attachments/assets/84f5d9dd-de71-4aa3-875f-a20d1870166f" />


---

### NFA

<img width="958" height="387" alt="image" src="https://github.com/user-attachments/assets/dae44711-4939-4c81-883e-c8956d1cc630" />


---

### DFA
<img width="951" height="424" alt="image" src="https://github.com/user-attachments/assets/445c9a82-2848-4ef6-86af-67d0e5d6dbb1" />


---

### Minimized DFA

<img width="956" height="380" alt="image" src="https://github.com/user-attachments/assets/845db19f-be81-40cc-8f55-f79d51941506" />


---

## Future Improvements

- Responsive User Interface
- Additional Compiler Phases
- Export Automata as Images
- Support for More Programming Languages
- Syntax Analysis Module

---

## Team Members

- Rabiya Gilani
- Faryha Fatima
- Ayesha Akbar
- Norr Fatima

---

## Acknowledgements

This project was developed as part of the **Theory of Automata** course and aims to provide an interactive learning platform for compiler construction and automata theory.

---

## License

This project is licensed under the MIT License.


