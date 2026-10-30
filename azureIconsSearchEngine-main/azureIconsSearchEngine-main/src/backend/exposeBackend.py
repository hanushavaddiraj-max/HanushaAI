from flask import Flask, jsonify, request, render_template
from querydb import return_results_from_db
from flask_cors import CORS

app = Flask(__name__)

CORS(app)


@app.route("/dbquery", methods=['POST'])
def return_results():
    data = request.json

    user_query=data.get('user_query')
    
    results = return_results_from_db(user_query)
    
    return jsonify(results)
    
    
if __name__=="main":
    app.run(debug=True)
    