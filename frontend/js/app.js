const API_URL = "http://127.0.0.1:3000";

const submissionForm = document.getElementById("submissionForm");
const submissionResult = document.getElementById("submissionResult");

const submissionIdInput = document.getElementById("submissionId");
const checkStatusButton = document.getElementById("checkStatusButton");
const statusResult = document.getElementById("statusResult");


submissionForm.addEventListener("submit", async function (event) {

    event.preventDefault();

    const studentRef = document.getElementById("studentRef").value.trim();
    const courseCode = document.getElementById("courseCode").value.trim();
    const assessment = document.getElementById("assessment").value.trim();

    const fileInput = document.getElementById("submissionFile");
    const file = fileInput.files[0];

    if (!file) {
        submissionResult.innerHTML =
            "<p>Please select a file.</p>";
        return;
    }

    const requestData = {
        student_ref: studentRef,
        course_code: courseCode,
        assessment: assessment,
        file_name: file.name,
        content_type: file.type,
        file_size_bytes: file.size
    };

    submissionResult.innerHTML =
        "<p>Submitting...</p>";

    try {

        const response = await fetch(`${API_URL}/submissions`, {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify(requestData)
        });

        const data = await response.json();

        if (!response.ok) {
            submissionResult.innerHTML = `
                <p><strong>Submission failed.</strong></p>
                <p>${data.error || "Unknown error"}</p>
            `;
            return;
        }

        submissionResult.innerHTML = `
            <p><strong>Submission created successfully.</strong></p>

            <p>
                <strong>Submission ID:</strong><br>
                ${data.submission_id}
            </p>

            <p>
                <strong>Status:</strong>
                <span class="status status-pending">
                    ${data.status}
                </span>
            </p>

            <p>
                <strong>Expires At:</strong><br>
                ${data.expires_at}
            </p>

            <p>
                <strong>Request ID:</strong><br>
                ${data.request_id}
            </p>
        `;

        submissionIdInput.value = data.submission_id;

    } catch (error) {

        console.error(error);

        submissionResult.innerHTML = `
            <p><strong>Unable to connect to the backend.</strong></p>
            <p>Check that SAM Local API is running.</p>
        `;
    }
});


checkStatusButton.addEventListener("click", async function () {

    const submissionId = submissionIdInput.value.trim();

    if (!submissionId) {
        statusResult.innerHTML =
            "<p>Please enter a submission ID.</p>";
        return;
    }

    statusResult.innerHTML =
        "<p>Checking status...</p>";

    try {

        const response = await fetch(
            `${API_URL}/submissions/${submissionId}`
        );

        const data = await response.json();

        if (!response.ok) {
            statusResult.innerHTML = `
                <p><strong>Unable to retrieve submission.</strong></p>
                <p>${data.error || "Unknown error"}</p>
            `;
            return;
        }

        // GetSubmission returns the record inside "submission"
        const submission = data.submission;

        const statusClass =
            submission.status === "ACCEPTED"
                ? "status-accepted"
                : submission.status === "REJECTED"
                ? "status-rejected"
                : submission.status === "EXPIRED"
                ? "status-expired"
                : "status-pending";

        statusResult.innerHTML = `
            <p>
                <strong>Submission ID:</strong><br>
                ${submission.submission_id}
            </p>

            <p>
                <strong>Student Reference:</strong>
                ${submission.student_ref}
            </p>

            <p>
                <strong>File:</strong>
                ${submission.file_name}
            </p>

            <p>
                <strong>Course:</strong>
                ${submission.course_code}
            </p>

            <p>
                <strong>Assessment:</strong>
                ${submission.assessment}
            </p>

            <p>
                <strong>Status:</strong>
                <span class="status ${statusClass}">
                    ${submission.status}
                </span>
            </p>
        `;

    } catch (error) {

        console.error(error);

        statusResult.innerHTML = `
            <p><strong>Unable to connect to the backend.</strong></p>
            <p>Check that SAM Local API is running.</p>
        `;
    }
});