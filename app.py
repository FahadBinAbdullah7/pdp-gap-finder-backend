<!DOCTYPE html>
<html>
<head>
    <title>PDP Comparison and Generation</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .section { margin-bottom: 20px; }
        .error { color: red; }
        textarea { width: 100%; height: 100px; }
    </style>
</head>
<body>
    <h1>PDP Comparison and Generation</h1>

    <!-- Step 1: Compare PDPs -->
    <div class="section">
        <h2>Step 1: Compare PDPs</h2>
        <form method="POST" enctype="multipart/form-data">
            <input type="hidden" name="action" value="compare">
            <label>Your PDP URL:</label><br>
            <input type="text" name="your_url" style="width: 100%;"><br>
            <label>Competitor PDP URL:</label><br>
            <input type="text" name="comp_url" style="width: 100%;"><br>
            <input type="submit" value="Compare PDPs">
        </form>
    </div>

    <!-- Display PDP Analysis -->
    {% if result.pdp_analysis %}
    <div class="section">
        <h2>PDP Analysis</h2>
        <pre>{{ result.pdp_analysis }}</pre>
    </div>
    {% endif %}

    <!-- Step 2: Upload PDF -->
    {% if result.pdp_analysis %}
    <div class="section">
        <h2>Step 2: Upload PDP Description PDF</h2>
        <form method="POST" enctype="multipart/form-data">
            <input type="hidden" name="action" value="upload">
            <input type="hidden" name="pdp_analysis" value="{{ result.pdp_analysis }}">
            <label>Upload PDF:</label><br>
            <input type="file" name="pdf_file" accept=".pdf"><br>
            <input type="submit" value="Upload PDF">
        </form>
    </div>
    {% endif %}

    <!-- Step 3: Specify Program and Generate SEO Keywords -->
    {% if result.pdf_text %}
    <div class="section">
        <h2>Step 3: Specify Program and Generate SEO Keywords</h2>
        <form method="POST" enctype="multipart/form-data">
            <input type="hidden" name="action" value="generate_seo">
            <input type="hidden" name="pdp_analysis" value="{{ result.pdp_analysis }}">
            <input type="hidden" name="pdf_text" value="{{ result.pdf_text }}">
            <label>Program Name:</label><br>
            <input type="text" name="program" value="{{ result.program }}"><br>
            <input type="submit" value="Generate SEO Keywords">
        </form>
    </div>
    {% endif %}

    <!-- Display SEO Keywords -->
    {% if result.seo_keywords %}
    <div class="section">
        <h2>SEO Keywords</h2>
        <form method="POST" enctype="multipart/form-data">
            <input type="hidden" name="action" value="generate_pdp">
            <input type="hidden" name="pdp_analysis" value="{{ result.pdp_analysis }}">
            <input type="hidden" name="pdf_text" value="{{ result.pdf_text }}">
            <input type="hidden" name="program" value="{{ result.program }}">
            <label>Edit SEO Keywords:</label><br>
            <textarea name="seo_keywords">{{ result.seo_keywords }}</textarea><br>
            <input type="submit" value="Generate PDP Description">
        </form>
    </div>
    {% endif %}

    <!-- Display Generated PDP Description -->
    {% if result.pdp_description %}
    <div class="section">
        <h2>Generated PDP Description</h2>
        <pre>{{ result.pdp_description }}</pre>
    </div>
    {% endif %}

    <!-- Display Errors -->
    {% if result.error %}
    <div class="error">{{ result.error }}</div>
    {% endif %}
</body>
</html>
