Name: movie app cst 205
Names of team members: Brandon Grimaldo, Caleb Stark, Eashwar Sridharan, Janira Martinez-Amador
Class: cst 205
Date: April 16th 2025
Date of completion: May 16th 2025
## How to run program

### Setup Instructions
1. Create a virtual environment:
   ```
   python -m venv venv
   ```

2. Activate the virtual environment:
   - Windows:
     ```
     .\venv\Scripts\activate
     ```
   - Mac/Linux:
     ```
     source venv/bin/activate
     ```

3. Install dependencies with specific versions to avoid compatibility issues:
   ```
   pip install Flask==2.0.1 requests==2.26.0 python-dotenv==1.0.0
   pip install werkzeug==2.0.1
   pip install supabase==1.0.3 httpx==0.24.1
   ```

4. Run the application:
   ```
   python app.py
   ```

5. Open your web browser and go to: http://127.0.0.1:5000/

### Troubleshooting
- If you see "ModuleNotFoundError", make sure your virtual environment is activated
- If you encounter any Werkzeug or Supabase related errors, use the specific versions mentioned above
- For Anaconda users: You may need to use `conda deactivate` before creating the virtual environment

Github Link: https://github.com/RaisinBranSnail/Movie-App
Trello: https://trello.com/invite/b/67fd8a4e413ca1f57a826735/ATTI057f94e891a24aa8a4715fab79f9d42b17C8B67D/cst205-group-project
Future work: Add video trailers
