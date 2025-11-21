# fix_imports.py
import re

# Fix views.py imports
with open('myapp/views.py', 'r') as f:
    content = f.read()

# Remove BlogPost and BlogComment from imports
content = re.sub(r",\s*BlogPost", "", content)
content = re.sub(r",\s*BlogComment", "", content)
content = re.sub(r"BlogPost,\s*", "", content)
content = re.sub(r"BlogComment,\s*", "", content)

# Remove blog-related view functions
content = re.sub(r'def blog_list.*?(?=def|\Z)', '', content, flags=re.DOTALL)
content = re.sub(r'def blog_detail.*?(?=def|\Z)', '', content, flags=re.DOTALL)
content = re.sub(r'def add_blog_comment.*?(?=def|\Z)', '', content, flags=re.DOTALL)

with open('myapp/views.py', 'w') as f:
    f.write(content)

print("✅ Removed BlogPost imports from views.py")