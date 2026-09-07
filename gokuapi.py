@app.route('/proxy')
def proxy():
    target_url = "http://professorxme.site/api.php"
    # Forward all query parameters
    params = request.args
    response = requests.get(target_url, params=params)
    return response.content, response.status_code
