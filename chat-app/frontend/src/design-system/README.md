# Design System - Chat App

## 📐 Arquitetura

Este design system segue uma arquitetura modular e escalável baseada em **Design Tokens** e **componentes reutilizáveis**.

### Estrutura de Pastas

```
src/design-system/
├── tokens/              # Design tokens (cores, espaçamentos, tipografia)
│   ├── colors.ts
│   ├── spacing.ts
│   ├── typography.ts
│   ├── radius.ts
│   ├── shadows.ts
│   ├── breakpoints.ts
│   └── index.ts
├── styles/              # Estilos globais e utilitários
│   ├── foundations.scss # CSS vars, reset, base styles
│   ├── utilities.scss   # Classes utilitárias
│   └── mixins.scss      # Mixins Sass reutilizáveis
├── components/          # Componentes do Design System
│   ├── DSChatInput/
│   │   ├── DSChatInput.vue
│   │   ├── DSChatInput.scss
│   │   └── index.ts
│   ├── DSChatHeader/
│   │   ├── DSChatHeader.vue
│   │   ├── DSChatHeader.scss
│   │   └── index.ts
│   ├── DSMessageBubble/
│   │   ├── DSMessageBubble.vue
│   │   ├── DSMessageBubble.scss
│   │   └── index.ts
│   ├── DSAttachmentMenu/    # Menu de anexos estilo WhatsApp
│   │   ├── DSAttachmentMenu.vue
│   │   └── index.ts
│   ├── DSVoiceRecorder/     # Gravador de voz com visualização
│   │   ├── DSVoiceRecorder.vue
│   │   └── index.ts
│   ├── DSUploader/          # Upload de arquivos drag-and-drop
│   │   ├── DSUploader.vue
│   │   └── index.ts
│   ├── DSCommandBar/        # Barra de comandos do Guru
│   │   ├── DSCommandBar.vue
│   │   └── index.ts
│   └── DSDateSeparator/     # Separador de data em mensagens
│       ├── DSDateSeparator.vue
│       └── index.ts
├── composables/         # Lógica reutilizável (Composition API)
│   ├── useChat.ts
│   └── useScrollToBottom.ts
└── types/               # TypeScript types compartilhados
```

## 🎨 Design Tokens

Os tokens são definidos em TypeScript e exportados como CSS Custom Properties (variáveis CSS) para consumo nos componentes.

### Como Usar

**Em TypeScript/Vue Script:**
```typescript
import { colors, spacing } from '@/design-system/tokens';
```

**Em CSS/SCSS:**
```scss
.my-component {
  color: var(--ds-color-primary);
  padding: var(--ds-spacing-md);
  border-radius: var(--ds-radius-md);
}
```

### Tokens Disponíveis

#### Cores
- `--ds-color-primary`, `--ds-color-secondary`
- `--ds-color-sent-message`, `--ds-color-received-message`
- `--ds-color-text-primary`, `--ds-color-text-secondary`
- `--ds-color-success`, `--ds-color-error`, `--ds-color-warning`

#### Espaçamentos
- `--ds-spacing-xs` (4px), `--ds-spacing-sm` (8px), `--ds-spacing-md` (12px)
- `--ds-spacing-lg` (16px), `--ds-spacing-xl` (20px), `--ds-spacing-xxl` (24px)

#### Tipografia
- `--ds-font-size-xs` (11px), `--ds-font-size-sm` (12px), `--ds-font-size-base` (14px)
- `--ds-font-weight-regular` (400), `--ds-font-weight-medium` (500), `--ds-font-weight-semibold` (600)

#### Bordas e Sombras
- `--ds-radius-sm`, `--ds-radius-md`, `--ds-radius-lg`
- `--ds-shadow-sm`, `--ds-shadow-md`, `--ds-shadow-lg`

## 🧩 Componentes

### Nomenclatura

- Prefixo `DS` para componentes do design system
- PascalCase: `DSChatInput`, `DSMessageBubble`
- Cada componente em sua própria pasta com `index.ts` para importação limpa

### Exemplo de Uso

```vue
<template>
  <DSChatInput
    v-model="message"
    @submit="handleSend"
    @typing="handleTyping"
  />
  
  <DSAttachmentMenu
    v-model="showMenu"
    @file-selected="handleFile"
  >
    <template #activator="{ props }">
      <v-btn icon v-bind="props">
        <v-icon>mdi-paperclip</v-icon>
      </v-btn>
    </template>
  </DSAttachmentMenu>
</template>

<script setup lang="ts">
// Importações via barrel export (named imports)
import { DSChatInput } from '@/design-system/components/DSChatInput';
import { DSAttachmentMenu } from '@/design-system/components/DSAttachmentMenu';
</script>
```

### Componentes Disponíveis

#### Layout e Navegação
- **DSChatHeader**: Cabeçalho do chat com avatar e ações
- **DSChatInput**: Input de mensagem com anexos e emoji

#### Mensagens
- **DSMessageBubble**: Bolha de mensagem (enviada/recebida)
- **DSDateSeparator**: Separador de data entre mensagens

#### Interações
- **DSAttachmentMenu**: Menu de seleção de tipo de anexo
- **DSVoiceRecorder**: Interface de gravação de áudio
- **DSUploader**: Componente de upload com drag-and-drop
- **DSCommandBar**: Barra de comandos e shortcuts do Guru

## 🛠️ Classes Utilitárias

Classes CSS prontas para uso rápido em templates:

```vue
<div class="u-flex-between u-gap-md u-padding-lg">
  <span>Item 1</span>
  <span>Item 2</span>
</div>
```

### Utilitários Disponíveis

**Layout:**
- `.u-flex-column`, `.u-flex-center`, `.u-flex-between`
- `.u-gap-xs`, `.u-gap-sm`, `.u-gap-md`, `.u-gap-lg`

**Espaçamento:**
- `.u-padding-sm`, `.u-padding-md`, `.u-padding-lg`

**Efeitos:**
- `.u-shadow-sm`, `.u-shadow-md`, `.u-shadow-lg`
- `.u-rounded-md`, `.u-rounded-lg`

**Scroll:**
- `.u-scrollable-y` (overflow-y com scrollbar estilizada)

**Safe Area:**
- `.u-safe-area-bottom` (padding-bottom com safe-area-inset)

## 🎯 Mixins Sass

Mixins reutilizáveis em arquivos `.scss`:

```scss
@use '@/design-system/styles/mixins' as mixins;

.my-component {
  @include mixins.ds-elevation(md);
  @include mixins.ds-rounded(lg);
  @include mixins.ds-scrollbar();
}
```

### Mixins Disponíveis

- `ds-elevation($level)` - Aplica sombra
- `ds-rounded($size)` - Aplica border-radius
- `ds-scrollbar($thumb, $track, $width)` - Estiliza scrollbar
- `ds-safe-area-bottom($gap)` - Padding com safe-area
- `ds-responsive($breakpoint)` - Media query

## 📱 Responsividade

Breakpoints definidos seguindo padrão mobile-first:

- `xs`: 0px (mobile portrait)
- `sm`: 600px (mobile landscape)
- `md`: 960px (tablet portrait)
- `lg`: 1264px (desktop)
- `xl`: 1904px (large desktop)

### Uso em SCSS

```scss
.component {
  padding: var(--ds-spacing-sm);

  @media (min-width: 960px) {
    padding: var(--ds-spacing-lg);
  }
}
```

## ✅ Boas Práticas

1. **NUNCA hardcodar valores** - Sempre usar tokens
   ```scss
   /* ❌ Ruim */
   .component { color: #075e54; }

   /* ✅ Bom */
   .component { color: var(--ds-color-primary); }
   ```

2. **Componentes DS em pastas próprias**
   ```
   DSChatInput/
   ├── DSChatInput.vue
   ├── DSChatInput.scss
   └── index.ts
   ```

3. **Estilos externos via `src`**
   ```vue
   <style scoped lang="scss" src="./DSChatInput.scss"></style>
   ```

4. **Importar via index.ts (named imports)**
   ```typescript
   // ✅ Bom - Named import via barrel
   import { DSChatInput } from '@/design-system/components/DSChatInput';
   import { DSAttachmentMenu } from '@/design-system/components/DSAttachmentMenu';

   // ❌ Evitar - Default import ou path completo
   import DSChatInput from '@/design-system/components/DSChatInput';
   import DSChatInput from '@/design-system/components/DSChatInput/DSChatInput.vue';
   ```

5. **Usar utilitários quando possível**
   ```vue
   <!-- Ao invés de criar classe customizada -->
   <div class="u-flex-between u-padding-md u-shadow-sm">
   ```

## 🔧 Configuração Vite

O Vite está configurado para injetar automaticamente os mixins em todos os arquivos SCSS:

```typescript
// vite.config.ts
css: {
  preprocessorOptions: {
    scss: {
      additionalData: '@use "@/design-system/styles/mixins" as mixins;\n'
    }
  }
}
```

## 📚 Referências

- [Vue 3 Style Guide](https://vuejs.org/style-guide/)
- [Design Tokens W3C](https://design-tokens.github.io/community-group/format/)
- [BEM Methodology](http://getbem.com/)
