# Guia de Contribuição

Obrigado por considerar contribuir para o Chat App! 🎉

## Como Contribuir

### Reportando Bugs

1. Verifique se o bug já foi reportado nas [Issues](https://github.com/cleberfarias/projeto_estudo/issues)
2. Abra uma nova issue incluindo:
   - Descrição clara do problema
   - Passos para reproduzir
   - Comportamento esperado vs. atual
   - Screenshots se aplicável
   - Ambiente (OS, navegador, versão do Node.js)

### Sugerindo Melhorias

1. Abra uma issue com a tag `enhancement`
2. Descreva a funcionalidade desejada
3. Explique por que seria útil
4. Se possível, sugira uma implementação

### Pull Requests

1. **Fork** o repositório
2. **Clone** seu fork localmente
3. **Crie uma branch** para sua feature:
   ```bash
   git checkout -b feature/minha-feature
   ```
4. **Faça suas alterações** seguindo os padrões do projeto
5. **Teste** suas mudanças:
   ```bash
   # Backend
   cd backend && npm run dev
   
   # Frontend
   cd frontend && npm run dev
   ```
6. **Commit** com mensagens descritivas:
   ```bash
   git commit -m "feat: adiciona funcionalidade X"
   ```
7. **Push** para seu fork:
   ```bash
   git push origin feature/minha-feature
   ```
8. Abra um **Pull Request** no repositório original

## Padrões de Código

### Commits

Seguimos o padrão [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` Nova funcionalidade
- `fix:` Correção de bug
- `docs:` Mudanças na documentação
- `style:` Formatação, ponto e vírgula, etc
- `refactor:` Refatoração de código
- `test:` Adição de testes
- `chore:` Manutenção, configuração

**Exemplos:**
```
feat: adiciona suporte a salas de chat
fix: corrige evento Socket.IO no frontend
docs: atualiza README com instruções de deploy
```

### TypeScript

- Use tipos explícitos sempre que possível
- Evite `any`
- Valide dados com Zod quando receber do cliente

### Vue/Frontend

- Use Composition API (`<script setup>`)
- Componentes em PascalCase
- Props e events tipados
- Mantenha componentes pequenos e focados

### Node/Backend

- Use ES6+ modules
- Async/await ao invés de callbacks
- Trate erros adequadamente
- Valide entrada de dados

## Estrutura de Branches

- `main` - Branch principal (protegida)
- `feature/*` - Novas funcionalidades
- `fix/*` - Correções de bugs
- `docs/*` - Documentação
- `refactor/*` - Refatorações

## Testes

Embora ainda não tenhamos cobertura de testes, PRs com testes são extremamente bem-vindos!

## Dúvidas?

Abra uma issue ou entre em contato através do GitHub.

Obrigado por contribuir! 💚
