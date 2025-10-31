import difflib

# File paths to compare
file1 = "api_fetched.html"
file2 = "test_script_fetched.html"

with open(file1, "r", encoding="utf-8") as f1, open(file2, "r", encoding="utf-8") as f2:
    html1 = f1.readlines()
    html2 = f2.readlines()

diff = difflib.unified_diff(html1, html2, fromfile=file1, tofile=file2)

print("\n--- Differences between api_fetched.html and test_script_fetched.html ---\n")
for line in diff:
    print(line, end="")
