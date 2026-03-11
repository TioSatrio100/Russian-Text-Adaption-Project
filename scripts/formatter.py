import textwrap

def format_output(text, max_width=85):
    text = '\n'.join([line for line in text.split('\n') if line.strip()])
    
    formatted_lines = []
    
    for line in text.split('\n'):
        line_stripped = line.strip()
        
        if not line_stripped:
            formatted_lines.append('')
        elif line_stripped.startswith(('ЭТАП', 'PHASE', 'STAGE')):
            formatted_lines.append('\n' + '═' * 60)
            formatted_lines.append(line_stripped)
            formatted_lines.append('═' * 60)
        elif len(line_stripped) > 0 and line_stripped[0].isdigit() and '.' in line_stripped[:3]:
            formatted_lines.append('\n' + line_stripped)
        elif len(line_stripped) > max_width:
            wrapped = textwrap.fill(
                line_stripped,
                width=max_width,
                initial_indent='',
                subsequent_indent=''
            )
            formatted_lines.append(wrapped)
        else:
            formatted_lines.append(line_stripped)
    
    return '\n'.join(formatted_lines)