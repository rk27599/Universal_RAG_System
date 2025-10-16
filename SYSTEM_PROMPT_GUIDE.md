# Material Studio Expert System Prompt Guide

## Overview

The Material Studio Expert System Prompt is a configurable feature that transforms the RAG system's LLM into a specialized technical assistant. It enforces citation-based responses, prevents hallucinations, and ensures answers are grounded strictly in the retrieved documentation.

**Status:** ✅ Fully Implemented (October 2025)

## Key Features

### 1. Default Behavior (ON by default)
- Automatically applied to all RAG queries with document context
- LLM acts as a Material Studio expert assistant
- Enforces strict grounding in retrieved documentation
- Requires citation of sources for all claims

### 2. User Configurable
- **Toggle ON/OFF:** Via Settings UI (Frontend)
- **Customize Prompt:** Optional custom system prompt editor
- **Persistent Settings:** Saved to browser localStorage
- **Live Updates:** No backend restart required

### 3. Citation-Based Responses
- Forces LLM to cite specific documentation sections
- References file names, function names, code examples
- Acknowledges limitations when context is insufficient
- Prevents fabrication of information not in retrieved docs

## How It Works

### Query Flow

```
1. User sends message with RAG enabled
   ↓
2. ChatInterface reads localStorage settings
   - useExpertPrompt (default: true)
   - customSystemPrompt (optional)
   ↓
3. Socket.IO sends message to backend with settings
   ↓
4. Backend retrieves relevant document chunks (top-k)
   ↓
5. If useExpertPrompt = true AND context exists:
   - Apply default Material Studio prompt (or custom)
   - Prepend to LLM context before document chunks
   ↓
6. LLM generates response following expert prompt rules
   ↓
7. Frontend displays citation-based, grounded response
```

### Backend Integration

**File:** [webapp/backend/api/chat.py](webapp/backend/api/chat.py)

```python
# Default Material Studio Expert Prompt (lines 24-93)
DEFAULT_MATERIAL_STUDIO_PROMPT = """You are an expert technical assistant specializing in Material Studio. Your role is to provide accurate, helpful answers about Material Studio using ONLY the retrieved documentation and code context provided to you.

## Core Principles

### 1. Accuracy and Grounding
- Answer questions using ONLY the information from the retrieved context below
- NEVER generate information that is not present in the provided documentation or code
- If the context doesn't contain enough information to answer completely, acknowledge this limitation
- When uncertain, explicitly state your uncertainty rather than guessing

### 2. Citation and Transparency
- Always cite specific sources when making claims (e.g., "According to the Forcite Module API documentation…")
- Reference specific code files, function names, or documentation sections when applicable
- If information comes from multiple sources, acknowledge all relevant sources

### 3. Response Quality
- Provide clear, concise answers (2–4 sentences for simple queries, longer for complex topics)
- Use proper formatting: code blocks for code snippets, bullet points for lists, headers for organization
- Include relevant code examples when they help clarify the answer
- Explain technical concepts in accessible language while maintaining accuracy

Remember: Only use information from the provided context. If you cannot answer based on the context, say so clearly."""

# Socket.IO message handler (lines 710-711, 827-836)
@socketio.on('send_message')
async def handle_send_message(data):
    # ... (authentication, validation)

    # Get expert prompt settings from client
    use_expert_prompt = data.get('useExpertPrompt', True)  # Default ON
    custom_system_prompt = data.get('customSystemPrompt', None)

    # ... (RAG retrieval, document context)

    # Apply system prompt if RAG enabled and context exists
    system_prompt = None
    if use_rag and document_context:
        if use_expert_prompt:
            # Use custom prompt if provided, otherwise default
            system_prompt = custom_system_prompt or DEFAULT_MATERIAL_STUDIO_PROMPT
            prompt_type = "custom" if custom_system_prompt else "default"
            logger.info(f"🎯 Using Material Studio expert system prompt ({prompt_type})")
        else:
            logger.info(f"ℹ️ Expert prompt disabled by user")

    # Send to LLM with system prompt
    # ...
```

### Frontend Integration

#### Settings UI Component

**File:** [webapp/frontend/src/components/Settings/PromptSettings.tsx](webapp/frontend/src/components/Settings/PromptSettings.tsx)

```typescript
export const PromptSettings: React.FC<PromptSettingsProps> = ({
  useExpertPrompt,
  onUseExpertPromptChange,
  customPrompt,
  onCustomPromptChange,
}) => {
  return (
    <Box>
      {/* Toggle Switch */}
      <FormControlLabel
        control={
          <Switch
            checked={useExpertPrompt}
            onChange={(e) => onUseExpertPromptChange(e.target.checked)}
          />
        }
        label="Use Material Studio Expert System Prompt"
      />

      {/* Alert: Expert Prompt Active */}
      {useExpertPrompt && (
        <Alert severity="info">
          The AI will cite sources, acknowledge limitations,
          and refuse to answer questions without sufficient documentation context.
        </Alert>
      )}

      {/* Expandable Custom Prompt Editor */}
      {useExpertPrompt && (
        <Accordion>
          <AccordionDetails>
            <TextField
              multiline
              rows={12}
              value={customPrompt || ''}
              onChange={(e) => onCustomPromptChange(e.target.value)}
              helperText="Leave empty to use default Material Studio expert prompt"
            />
          </AccordionDetails>
        </Accordion>
      )}
    </Box>
  );
};
```

#### Settings Persistence

**File:** [webapp/frontend/src/components/Settings/ModelSettings.tsx](webapp/frontend/src/components/Settings/ModelSettings.tsx)

```typescript
// Initialize from localStorage (lines 88-94)
const [useExpertPrompt, setUseExpertPrompt] = useState(() => {
  const saved = localStorage.getItem('useExpertPrompt');
  return saved !== null ? JSON.parse(saved) : true; // Default ON
});

const [customSystemPrompt, setCustomSystemPrompt] = useState(() => {
  return localStorage.getItem('customSystemPrompt') || '';
});

// Persist to localStorage (lines 141-147)
useEffect(() => {
  localStorage.setItem('useExpertPrompt', JSON.stringify(useExpertPrompt));
}, [useExpertPrompt]);

useEffect(() => {
  localStorage.setItem('customSystemPrompt', customSystemPrompt);
}, [customSystemPrompt]);
```

#### Chat Interface Integration

**File:** [webapp/frontend/src/components/Chat/ChatInterface.tsx](webapp/frontend/src/components/Chat/ChatInterface.tsx)

```typescript
const handleSendMessage = useCallback(async () => {
  // ... (validation)

  // Read expert prompt settings from localStorage
  const useExpertPrompt = localStorage.getItem('useExpertPrompt');
  const customSystemPrompt = localStorage.getItem('customSystemPrompt');

  // Send message with expert prompt settings
  const success = await sendMessage(message, {
    ...configRef.current,
    useExpertPrompt: useExpertPrompt !== null ? JSON.parse(useExpertPrompt) : true,
    customSystemPrompt: customSystemPrompt || undefined,
  });
}, [messageInput, isLoading, sendMessage]);
```

## Configuration Guide

### For Users

#### Option 1: Use Default Expert Prompt (Recommended)

1. Open Settings (gear icon in chat interface)
2. Scroll to "System Prompt Settings"
3. Ensure "Use Material Studio Expert System Prompt" is **enabled** (default)
4. Leave custom prompt **empty** to use the default
5. Chat responses will now cite sources and stay grounded

#### Option 2: Customize Expert Prompt

1. Open Settings → System Prompt Settings
2. Enable "Use Material Studio Expert System Prompt"
3. Expand "Customize System Prompt (Optional)"
4. Edit the prompt text to adjust AI behavior
5. Click outside or switch tabs to auto-save
6. Test with a RAG query to verify behavior

#### Option 3: Disable Expert Prompt

1. Open Settings → System Prompt Settings
2. Toggle **OFF** "Use Material Studio Expert System Prompt"
3. LLM will use general behavior without strict grounding
4. Warning: May lead to hallucinations or fabricated information

### For Developers

#### Modify Default Prompt

Edit [webapp/backend/api/chat.py](webapp/backend/api/chat.py):

```python
DEFAULT_MATERIAL_STUDIO_PROMPT = """Your custom system prompt here..."""
```

#### Add New Prompt Presets

Extend `PromptSettings.tsx` with dropdown menu:

```typescript
const PROMPT_PRESETS = {
  material_studio: DEFAULT_PROMPT,
  python_expert: "You are a Python expert...",
  general: "You are a helpful assistant...",
};
```

#### Adjust Default Behavior

Change default from ON to OFF in `ModelSettings.tsx`:

```typescript
const [useExpertPrompt, setUseExpertPrompt] = useState(() => {
  const saved = localStorage.getItem('useExpertPrompt');
  return saved !== null ? JSON.parse(saved) : false; // Changed to false
});
```

## Example Responses

### With Expert Prompt (Default)

**User:** "How do I run a Forcite energy calculation?"

**LLM Response:**
```
According to the Forcite Module API documentation, you can run an energy
calculation using the following code:

from Materials.Forcite import ForciteEnergy

calc = ForciteEnergy()
results = calc.run(structure)

The `ForciteEnergy` class is documented in the "Forcite Module Reference"
section. The `run()` method takes a Structure object as input and returns
energy results including potential energy, kinetic energy, and total energy.

If you need more specific details about force field selection or convergence
criteria, please let me know and I can search for additional documentation.
```

**Analysis:**
- ✅ Cites specific documentation section ("Forcite Module API documentation")
- ✅ Provides code example from retrieved context
- ✅ Acknowledges availability of additional information
- ✅ No fabricated information

### Without Expert Prompt

**User:** "How do I run a Forcite energy calculation?"

**LLM Response:**
```
To run a Forcite energy calculation in Material Studio, follow these steps:

1. Open Material Studio and load your structure
2. Go to Modules → Forcite → Energy
3. Select your force field (COMPASS, PCFF, etc.)
4. Configure calculation settings in the dialog
5. Click "Run" to start the calculation
6. Results will appear in the output panel

You can also automate this with Python scripts using the Materials Scripting
API. Make sure your structure is properly prepared before running calculations.
```

**Analysis:**
- ❌ May contain fabricated steps not in documentation
- ❌ No source citations
- ❌ Assumes GUI workflow without verifying against docs
- ❌ Potential hallucinations about API details

## Troubleshooting

### Issue: Expert Prompt Not Working

**Symptoms:**
- LLM responses don't cite sources
- Backend logs don't show "🎯 Using Material Studio expert system prompt"

**Solutions:**

1. **Check Settings:**
   - Open Settings → System Prompt Settings
   - Verify toggle is ON
   - Check browser console for localStorage errors

2. **Check Backend Logs:**
   ```bash
   cd webapp/backend
   tail -f logs/app.log | grep "expert"
   ```
   - Should see: `🎯 Using Material Studio expert system prompt (default)`
   - If not, check Socket.IO connection

3. **Clear Browser Cache:**
   ```javascript
   // Browser console
   localStorage.removeItem('useExpertPrompt');
   localStorage.removeItem('customSystemPrompt');
   location.reload();
   ```

4. **Verify RAG Context:**
   - Expert prompt only applies when document context exists
   - Check that documents are uploaded and indexed
   - Verify query similarity scores > threshold (0.70)

### Issue: Custom Prompt Not Saving

**Symptoms:**
- Custom prompt text resets after page refresh
- localStorage shows old values

**Solutions:**

1. **Check Browser Permissions:**
   - Ensure site can access localStorage
   - Check for "Block third-party cookies" settings

2. **Verify localStorage Size:**
   ```javascript
   // Browser console
   console.log(localStorage.getItem('customSystemPrompt')?.length);
   ```
   - Limit: ~5-10 MB per domain (varies by browser)

3. **Test Persistence:**
   ```javascript
   // Browser console
   localStorage.setItem('test', 'value');
   console.log(localStorage.getItem('test')); // Should print "value"
   ```

### Issue: LLM Ignores System Prompt

**Symptoms:**
- LLM generates responses without citations despite expert prompt
- Response format doesn't match prompt instructions

**Possible Causes:**

1. **LLM Context Length Exceeded:**
   - System prompt + document context + history > model limit
   - Solution: Reduce top-k sources or conversation history

2. **Model Doesn't Support System Messages:**
   - Some models ignore system prompts
   - Solution: Switch to a model that respects system messages (e.g., GPT-4, Mixtral)

3. **Prompt Conflict:**
   - Custom prompt contradicts retrieved document instructions
   - Solution: Review custom prompt for conflicting directives

## Best Practices

### Writing Custom Prompts

1. **Be Specific:** Clearly define expected behavior
   ```
   ❌ "Be helpful and accurate"
   ✅ "Answer using ONLY information from retrieved documentation"
   ```

2. **Enforce Citations:** Explicitly require source references
   ```
   ✅ "Always cite specific documents, sections, or code files"
   ```

3. **Handle Edge Cases:** Define behavior when context is insufficient
   ```
   ✅ "If context doesn't contain enough information, say: 'I cannot find sufficient information in the documentation to answer this question.'"
   ```

4. **Test Iteratively:** Verify custom prompts with diverse queries
   - Test with queries that have good context (high similarity)
   - Test with queries that lack context (low similarity)
   - Test with ambiguous or multi-part questions

### System Prompt Design Principles

1. **Grounding First:** Prioritize accuracy over creativity
2. **Transparency:** Encourage LLM to acknowledge limitations
3. **Structure:** Use clear sections and formatting in prompt
4. **Examples:** Include example responses if needed
5. **Brevity:** Keep prompts concise (< 500 tokens if possible)

## API Reference

### Socket.IO Parameters

**Event:** `send_message`

**Parameters:**
```typescript
{
  conversationId: string;
  content: string;
  model: string;
  temperature: number;
  maxTokens: number;
  useRAG: boolean;
  topK: number;
  documentIds?: string[];
  useExpertPrompt?: boolean;       // Default: true
  customSystemPrompt?: string;     // Default: null
}
```

### Frontend TypeScript Types

```typescript
interface SendMessageOptions {
  model?: string;
  temperature?: number;
  maxTokens?: number;
  useRAG?: boolean;
  topK?: number;
  documentIds?: string[];
  useExpertPrompt?: boolean;       // Default: true
  customSystemPrompt?: string;     // Optional custom prompt
}
```

### localStorage Keys

```typescript
localStorage.getItem('useExpertPrompt')      // "true" | "false" (JSON string)
localStorage.getItem('customSystemPrompt')   // string | "" (empty = use default)
```

## Future Enhancements

### Planned Features

1. **Prompt Presets:** Dropdown menu with predefined expert prompts
2. **Dynamic Prompt Injection:** Inject document metadata into system prompt
3. **Multi-Language Support:** Expert prompts for different languages
4. **Prompt Analytics:** Track which prompts lead to better responses
5. **A/B Testing UI:** Compare responses with/without expert prompt side-by-side

### Community Contributions

Want to improve the expert prompt system? Consider:

- **Sharing Custom Prompts:** Contribute effective custom prompts for different domains
- **Testing Edge Cases:** Report scenarios where expert prompt fails
- **Performance Metrics:** Measure citation accuracy and hallucination reduction
- **UI/UX Improvements:** Suggest better ways to configure prompts

## References

- **Backend Implementation:** [webapp/backend/api/chat.py](webapp/backend/api/chat.py)
- **Frontend UI Component:** [webapp/frontend/src/components/Settings/PromptSettings.tsx](webapp/frontend/src/components/Settings/PromptSettings.tsx)
- **Settings Persistence:** [webapp/frontend/src/components/Settings/ModelSettings.tsx](webapp/frontend/src/components/Settings/ModelSettings.tsx)
- **Chat Integration:** [webapp/frontend/src/components/Chat/ChatInterface.tsx](webapp/frontend/src/components/Chat/ChatInterface.tsx)
- **Related Documentation:** [CLAUDE.md](CLAUDE.md), [BGE_M3_MIGRATION_GUIDE.md](BGE_M3_MIGRATION_GUIDE.md)

---

**Last Updated:** 2025-10-16
**Status:** ✅ Production Ready
**Maintainer:** RAG System Development Team
