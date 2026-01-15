# AI Knowledge Assistant - Streamlit RAG Application

A beautiful, interactive chat application that allows you to query your OpenAI vector stores using Retrieval Augmented Generation (RAG).

## 🌟 Features

- **📚 Multiple Knowledge Bases**: Switch between different vector stores seamlessly
- **💬 Interactive Chat Interface**: Natural conversation with your documents
- **🔍 Intelligent Search**: Powered by OpenAI's file_search tool
- **📝 Source Citations**: Get references to the source documents
- **🎨 Modern UI**: Clean, professional interface with custom styling
- **💾 Session Management**: Maintains conversation context

## 🚀 Quick Start

### 1. Installation

Make sure you have all dependencies installed:

```bash
pip install -r requirements.txt
```

### 2. Environment Setup

Ensure your `.env` file contains:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4-turbo  # or your preferred model
```

### 3. Run the Application

```bash
streamlit run app.py
```

The app will automatically open in your browser at `http://localhost:8501`

## 📖 How to Use

1. **Select a Knowledge Base**: Choose from your available vector stores in the sidebar
2. **Ask Questions**: Type your question in the chat input at the bottom
3. **Get Answers**: The AI assistant will search your documents and provide detailed, cited responses
4. **Continue Conversation**: Ask follow-up questions - the assistant maintains context
5. **Switch Knowledge Bases**: Change vector stores anytime to query different document sets
6. **Clear History**: Use the "Clear Chat History" button to start fresh

## 🏗️ Architecture

The application uses:

- **Streamlit**: For the web interface
- **OpenAI Assistants API**: For intelligent conversation management
- **Vector Stores**: For document storage and retrieval
- **File Search Tool**: For RAG capabilities

### Workflow:

1. User selects a vector store
2. App creates an Assistant linked to that vector store
3. User asks a question
4. Assistant searches the vector store for relevant content
5. OpenAI generates a response based on retrieved documents
6. Response is displayed with citations

## 🎨 UI Components

### Sidebar
- **Knowledge Base Selector**: Choose which vector store to query
- **Store Details**: View information about the selected store
- **Model Info**: Current OpenAI model being used
- **Clear Chat**: Reset conversation history
- **About Section**: App information

### Main Area
- **Chat Interface**: Display conversation history
- **Message Input**: Enter your questions
- **Suggested Questions**: Quick-start prompts

## 🔧 Customization

### Change the Model

Edit your `.env` file:
```env
OPENAI_MODEL=gpt-4o  # or another model
```

### Modify Assistant Instructions

In `app.py`, find the `create_assistant()` function and customize the `instructions` parameter:

```python
instructions="""Your custom instructions here..."""
```

### Styling

Custom CSS is in the `st.markdown()` section at the top of `app.py`. Modify colors, spacing, and other visual elements there.

## 📋 Requirements

- Python 3.8+
- OpenAI API key
- At least one configured vector store with uploaded documents

## 🐛 Troubleshooting

### "No vector stores found"
- Make sure you've created vector stores using the `openai_1.ipynb` notebook
- Verify your OpenAI API key is correct

### "Error creating assistant"
- Check your API key has access to the Assistants API
- Ensure the vector store ID is valid

### App won't start
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check that port 8501 is available

## 💡 Tips

- **Be Specific**: Ask detailed questions for better responses
- **Use Context**: The assistant maintains conversation history
- **Check Citations**: Look for source references in responses
- **Try Different Stores**: Each knowledge base has different content

## 📊 Performance

- First response may take 5-10 seconds as documents are searched
- Subsequent responses are typically faster
- Response time depends on document size and complexity

## 🔐 Security

- Never commit your `.env` file
- Keep your OpenAI API key secure
- The app runs locally - no data is sent anywhere except OpenAI

## 📝 License

This project is for educational and demonstration purposes.

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section
2. Verify your vector stores have uploaded files
3. Ensure your OpenAI API account has credits

---

**Built with ❤️ using Streamlit and OpenAI**
