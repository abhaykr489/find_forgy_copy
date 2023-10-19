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

    $('#uploadForm').submit(function(event){
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
                if (response.error) {
                    var errorMessage = (response.responseJSON && response.responseJSON.error) ? response.responseJSON.error : 'Unknown error occurred.';
                    $('#result').html('<p class="error">Error: ' + errorMessage + '</p>');
                } else {
                    var formattedForgeryType = response.forgery_type.replace(/, /g, '-').replace(/,([^,]*)$/, '-$1');
                    $('#result').html('<p class="success">Forgery detected successfully. Accuracy: ' + response.accuracy.toFixed(2) + '%, Type of forgery: ' + formattedForgeryType + ', ' + response.forgery_percentage.toFixed(2) + '%</p>');

                    if (response.forgery_image_data) {
                        // If forgery image data is available, display the modified image with forgery areas
                        $('#imagePreview').html('<img src="data:image/jpeg;base64,' + response.forgery_image_data + '" alt="Modified Image">');
                    } else if (response.marked_image_path) {
                        // If marked image path is available, display the modified image with forgery areas
                        $('#imagePreview').html('<img src="' + response.marked_image_path + '" alt="Modified Image">');
                    }
                    // Display forgery information (percentage and types)
                    $('#forgeryInfo').html('<p>Forgery Percentage: ' + response.forgery_percentage.toFixed(2) + '%</p>');
                    $('#forgeryInfo').append('<p>Forgery Types: ' + response.forgery_type + '</p>');
                }
                isProcessing = false;
                $('#submitBtn').prop('disabled', false); // Re-enable the submit button
            },
            error: function(error){
                var errorMessage = (error.responseJSON && error.responseJSON.error) ? error.responseJSON.error : 'Unknown error occurred.';
                $('#result').html('<p class="error">Error: ' + errorMessage + '</p>');
                isProcessing = false;
                $('#submitBtn').prop('disabled', false); // Re-enable the submit button
            }
        });

        return false;
    });
});
