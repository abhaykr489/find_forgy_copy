$(document).ready(function(){
    var isProcessing = false; // Flag to prevent multiple submissions

    $('#fileInput').change(function(event){
        var input = event.target;
        var reader = new FileReader();
        reader.onload = function(){
            var dataURL = reader.result;
            $('#imagePreview').html('<img src="' + dataURL + '" alt="Chosen Image">');
        };
        reader.readAsDataURL(input.files[0]);
    });

    $('#fileInput').on('change', function(event){
        event.preventDefault();

        if (isProcessing) {
            return;
        }

        isProcessing = true;  // Set the flag to true to indicate processing
        $('#submitBtn').prop('disabled', true);

        var formData = new FormData($('#uploadForm')[0]);

        $.ajax({
            url: '/upload',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response){
                console.log(response); //debug
                // Inside the success callback function
                if (response.forgery_areas && response.forgery_areas.length > 0) {
                    // Loop through forgery areas and draw colored rectangles
                    response.forgery_areas.forEach(function(area, index) {
                        var forgeryArea = area[0];
                        var color = area[1];

                        var x = forgeryArea[0];
                        var y = forgeryArea[1];
                        var width = forgeryArea[2] - x;
                        var height = forgeryArea[3] - y;

                        // Draw colored rectangles for forgery areas
                        var canvas = document.createElement('canvas');
                        canvas.width = $('#imagePreview img').width();
                        canvas.height = $('#imagePreview img').height();
                        var ctx = canvas.getContext('2d');
                        ctx.strokeStyle = color; // Set the rectangle color
                        ctx.lineWidth = 3;
                        ctx.strokeRect(x, y, width, height);

                        // Append the canvas element to the imagePreviewContainer
                        $('#imagePreviewContainer').append(canvas);
                    });
                }

                // Display forgery types
                if (response.forgery_type) {
                    $('#result').html('<p class="success">Forgery Detected: ' + response.forgery_type + '</p>');
                } else {
                    $('#result').html('<p class="success">No forgery detected.</p>');
                }

                // Display original and forgery images side by side
                var originalImage = '<img src="' + $('#imagePreview img').attr('src') + '" alt="Original Image">';
                var forgeryImage = '<img src="' + response.forgery_image_path + '" alt="Forgery Image">';
                $('#imageContainer').html(originalImage + forgeryImage);

                isProcessing = false;
                $('#submitBtn').prop('disabled', false); // Re-enable the submit button
            },
            error: function(error){
                console.log(error); // debug
                var errorMessage = (error.responseJSON && error.responseJSON.error) ? error.responseJSON.error : 'Unknown error occurred.';
                $('#result').html('<p class="error">Error: ' + errorMessage + '</p>');
                isProcessing = false;
                $('#submitBtn').prop('disabled', false); // Re-enable the submit button
            }
        });

        return false;
    });
});
