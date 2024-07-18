<?php
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $to = "fgcid185496@gmail.com";  // Your email address
    $subject = "Contact Form Submission: " . $_POST['subject'];
    $name = $_POST['name'];
    $email = $_POST['email'];
    $message = $_POST['message'];

    $headers = "From: " . $email . "\r\n";
    $headers .= "Reply-To: " . $email . "\r\n";
    $headers .= "Content-type: text/html; charset=UTF-8" . "\r\n";

    $full_message = "<h2>Contact Form Submission</h2>";
    $full_message .= "<p><strong>Name:</strong> " . $name . "</p>";
    $full_message .= "<p><strong>Email:</strong> " . $email . "</p>";
    $full_message .= "<p><strong>Message:</strong><br>" . nl2br($message) . "</p>";

    if (mail($to, $subject, $full_message, $headers)) {
        echo "<script>alert('Your message has been sent. Thank you!'); window.location.href = 'index.html';</script>";
    } else {
        echo "<script>alert('There was an error sending your message. Please try again later.'); window.location.href = 'index.html';</script>";
    }
} else {
    echo "Invalid request method.";
}
?>
