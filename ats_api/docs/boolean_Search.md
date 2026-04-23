# Boolean Search for LinkedIn — AI Instruction Guide

Reference document for AI-generated boolean search strings targeting LinkedIn candidate sourcing.

---

## Operators

### AND — Narrow (both terms required)

Requires ALL connected terms to appear in the profile. More ANDs = fewer, more specific results.

```
"Software Engineer" AND "Python"
```

Result: only profiles containing both exact terms.

**Default behavior:** LinkedIn treats spaces as implicit AND. `Software Engineer` = `Software AND Engineer`. Use explicit AND when combining with other operators.

### OR — Expand (any term accepted)

Accepts ANY of the connected terms. More ORs = broader results. Use for synonyms, alternate titles, and equivalent skills.

```
"Frontend Developer" OR "Front-End Developer" OR "UI Developer" OR "Front End Engineer"
```

Result: profiles with any of these title variations.

### NOT — Exclude (remove unwanted results)

Removes profiles containing the specified term. Use sparingly — over-excluding narrows results too much.

```
"Marketing Manager" NOT "Intern" NOT "Freelance"
```

Result: marketing managers excluding interns and freelancers.

---

## Modifiers

### Quotation Marks `" "` — Exact phrase match

Searches the exact phrase in the exact order. **Required for multi-word terms.**

```
"Product Manager"        ✅ finds exact title
Product Manager          ❌ finds "Product" and "Manager" separately
```

### Parentheses `( )` — Group logic

Groups terms to control operator precedence. **Always wrap OR groups in parentheses when combined with AND.**

```
("Software Engineer" OR "Software Developer") AND ("Python" OR "Java") AND ("São Paulo" OR "Remote")
```

Without parentheses, the logic becomes ambiguous and produces unpredictable results.

**Rule:** If the string contains OR anywhere, it must be inside parentheses.

### Asterisk `*` — Wildcard (Google only)

Truncates or fills blanks. **Does not work on LinkedIn.** Only for Google X-Ray searches.

```
Develop*  →  developer, development, developing
```

---

## LinkedIn-Specific Rules

1. **Supported operators:** AND, OR, NOT, `" "`, `( )`
2. **NOT supported:** asterisk `*`, `NEAR`, `site:`, `filetype:`, `intitle:`
3. **Case sensitivity:** operators AND, OR, NOT must be UPPERCASE
4. **Search fields:** Keywords, Title, First Name, Last Name, Company
5. **Max string length:** ~1000 characters (practical limit)
6. **Implicit AND:** two words without operator are treated as AND
7. **Nested parentheses:** LinkedIn supports simple nesting, avoid deep nesting (max 2 levels)

---

## Construction Strategy

### Step 1 — Define the target role

Identify the primary job title and all common variations (synonyms, abbreviations, alternative nomenclatures in both English and Portuguese).

```
("Desenvolvedor Backend" OR "Backend Developer" OR "Back-End Developer" OR "Server-Side Developer" OR "Desenvolvedor Back-End")
```

### Step 2 — Add required skills (AND)

Connect essential/mandatory skills with AND. These are non-negotiable requirements.

```
AND ("Python" OR "Node.js" OR "Java")
```

### Step 3 — Add desirable skills (OR inside AND)

Desirable skills expand the pool. Group alternatives with OR inside a single AND block.

```
AND ("AWS" OR "GCP" OR "Azure" OR "Docker" OR "Kubernetes")
```

### Step 4 — Add location (if not remote)

```
AND ("São Paulo" OR "SP" OR "Campinas" OR "Remote")
```

### Step 5 — Add seniority (if relevant)

```
AND ("Sênior" OR "Senior" OR "Sr." OR "Lead" OR "Staff")
```

### Step 6 — Exclude noise (NOT)

Remove common false positives. Use only when you know specific terms pollute results.

```
NOT "Intern" NOT "Estágio" NOT "Freelance" NOT "Professor"
```

---

## Complete String Patterns

### Pattern: Technical Role

```
("Software Engineer" OR "Desenvolvedor" OR "Developer") AND ("Sênior" OR "Senior" OR "Pleno") AND ("React" OR "Angular" OR "Vue.js") AND ("TypeScript" OR "JavaScript") AND ("São Paulo" OR "Remote") NOT "Intern" NOT "Estágio" NOT "Freelance"
```

### Pattern: Management Role

```
("Engineering Manager" OR "Tech Lead" OR "Head of Engineering" OR "Gerente de Engenharia" OR "CTO") AND ("Software" OR "Technology" OR "Development") AND ("Team" OR "Squad" OR "Equipe") NOT "Recruiter" NOT "Freelance"
```

### Pattern: Broad Role with Industry Filter

```
("Data Scientist" OR "Machine Learning Engineer" OR "Cientista de Dados" OR "ML Engineer") AND ("Python" OR "R") AND ("TensorFlow" OR "PyTorch" OR "Scikit-learn") NOT "Student" NOT "Intern"
```

### Pattern: Sales/Business Role

```
("Account Executive" OR "Executivo de Contas" OR "Sales Manager" OR "Gerente Comercial") AND ("SaaS" OR "B2B" OR "Enterprise") AND ("CRM" OR "Salesforce" OR "HubSpot") NOT "Intern" NOT "Estágio"
```

---

## Common Mistakes to Avoid

| Mistake | Problem | Fix |
|---|---|---|
| Missing quotes on multi-word terms | `Project Manager` matches words separately | `"Project Manager"` |
| OR without parentheses | `Java OR Python AND Senior` is ambiguous | `(Java OR Python) AND Senior` |
| Overusing NOT | Too many exclusions eliminate good candidates | Max 3-4 NOT clauses |
| Ignoring synonyms | `Developer` misses `Engineer`, `Desenvolvedor` | Group all variations with OR |
| Only English terms | Brazilian profiles use Portuguese titles | Include both languages |
| Too many AND clauses | No candidate matches all 10 requirements | Max 4-5 AND groups, use OR for desirables |

---

## Skill Variation Map

When building strings, include common variations:

| Concept | Variations |
|---|---|
| Frontend | `"Frontend" OR "Front-End" OR "Front End" OR "UI Developer" OR "Desenvolvedor Frontend"` |
| Backend | `"Backend" OR "Back-End" OR "Back End" OR "Server-Side" OR "Desenvolvedor Backend"` |
| Fullstack | `"Fullstack" OR "Full-Stack" OR "Full Stack" OR "Desenvolvedor Fullstack"` |
| DevOps | `"DevOps" OR "SRE" OR "Site Reliability" OR "Infrastructure Engineer" OR "Platform Engineer"` |
| Data | `"Data Engineer" OR "Engenheiro de Dados" OR "Data Scientist" OR "Cientista de Dados" OR "Analytics Engineer"` |
| Product | `"Product Manager" OR "PM" OR "Gerente de Produto" OR "Product Owner" OR "PO"` |
| Design | `"UX Designer" OR "UI Designer" OR "Product Designer" OR "UX/UI" OR "Designer de Produto"` |
| HR/People | `"HR" OR "Human Resources" OR "People" OR "Recursos Humanos" OR "RH" OR "Talent"` |
| Project Mgmt | `"Project Manager" OR "Gerente de Projetos" OR "Scrum Master" OR "Agile Coach"` |
| QA | `"QA" OR "Quality Assurance" OR "Test Engineer" OR "SDET" OR "Analista de Testes"` |

## Seniority Variation Map

| Level | Variations |
|---|---|
| Junior | `"Júnior" OR "Junior" OR "Jr." OR "Jr" OR "Entry Level"` |
| Mid | `"Pleno" OR "Mid" OR "Mid-Level" OR "Intermediate"` |
| Senior | `"Sênior" OR "Senior" OR "Sr." OR "Sr" OR "Experienced"` |
| Lead | `"Lead" OR "Tech Lead" OR "Team Lead" OR "Líder Técnico"` |
| Manager | `"Manager" OR "Gerente" OR "Head" OR "Director" OR "Diretor"` |
| Specialist | `"Especialista" OR "Specialist" OR "Expert" OR "Principal" OR "Staff"` |

---

## Google X-Ray Search (for profiles outside LinkedIn limits)

When LinkedIn free plan limits results, use Google to search LinkedIn profiles directly.

### Base syntax

```
site:linkedin.com/in "keyword1" AND "keyword2"
```

### Full example

```
site:linkedin.com/in ("Software Engineer" OR "Desenvolvedor") AND ("Python" OR "Java") AND "São Paulo" NOT "Intern"
```

### Extra Google operators (not available on LinkedIn)

| Operator | Usage | Example |
|---|---|---|
| `site:` | Search within a specific site | `site:linkedin.com/in` |
| `filetype:` | Filter by file type | `filetype:pdf "curriculum"` |
| `intitle:` | Term must be in page title | `intitle:"Software Engineer"` |
| `*` | Wildcard / fill the blank | `"* Engineer" AND Python` |

---

## Construction Checklist

Before outputting a boolean string, verify:

- [ ] All multi-word terms are in double quotes `" "`
- [ ] All OR groups are inside parentheses `( )`
- [ ] Operators AND, OR, NOT are UPPERCASE
- [ ] Both Portuguese and English title variations are included
- [ ] Seniority level synonyms are grouped with OR
- [ ] Max 4-5 AND groups (essential requirements only)
- [ ] Max 3-4 NOT exclusions
- [ ] No asterisks `*` if targeting LinkedIn (only for Google X-Ray)
- [ ] String is under ~1000 characters
- [ ] No nested parentheses deeper than 2 levels
