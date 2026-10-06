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
        "<p>Creating submission...</p>";

    try {

        // --------------------------------------------------
        // STEP 1: Create the submission record
        // --------------------------------------------------

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
                <p>${data.error || data.message || "Unknown error"}</p>
            `;
            return;
        }

        const submissionId = data.submission_id;

        submissionIdInput.value = submissionId;

        submissionResult.innerHTML = `
            <p><strong>Submission created.</strong></p>
            <p>Uploading actual file...</p>
        `;


        // --------------------------------------------------
        // STEP 2: Convert the actual file to Base64
        // --------------------------------------------------

        const fileBase64 = await fileToBase64(file);


        // --------------------------------------------------
        // STEP 3: Upload the actual file
        // --------------------------------------------------

        const uploadResponse = await fetch(
            `${API_URL}/submissions/${submissionId}/upload`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/octet-stream",
                    "X-File-Name": file.name
                },

                body: fileBase64
            }
        );

        const uploadData = await uploadResponse.json();

        if (!uploadResponse.ok) {
            submissionResult.innerHTML = `
                <p><strong>Submission record created.</strong></p>

                <p>
                    <strong>Submission ID:</strong><br>
                    ${submissionId}
                </p>

                <p><strong>File upload failed.</strong></p>

                <p>
                    ${uploadData.error ||
                      uploadData.message ||
                      "Unknown upload error"}
                </p>
            `;
            return;
        }


        // --------------------------------------------------
        // STEP 4: Display successful upload
        // --------------------------------------------------

        submissionResult.innerHTML = `
            <p><strong>File submitted successfully.</strong></p>

            <p>
                <strong>Submission ID:</strong><br>
                ${submissionId}
            </p>

            <p>
                <strong>File:</strong>
                ${uploadData.file_name}
            </p>

            <p>
                <strong>Uploaded Size:</strong>
                ${uploadData.file_size_bytes} bytes
            </p>

            <p>
                <strong>Storage:</strong>
                ${uploadData.storage}
            </p>

            <p>
                <strong>Status:</strong>
                <span class="status status-pending">
                    ${data.status}
                </span>
            </p>

            <p>
                <strong>Request ID:</strong><br>
                ${data.request_id}
            </p>
        `;

    } catch (error) {

        console.error(error);

        submissionResult.innerHTML = `
            <p><strong>Unable to connect to the backend.</strong></p>
            <p>Check that SAM Local API is running.</p>
        `;
    }
});


// ----------------------------------------------------------
// Convert browser File object to Base64
// ----------------------------------------------------------

function fileToBase64(file) {

    return new Promise((resolve, reject) => {

        const reader = new FileReader();

        reader.onload = function () {

            const result = reader.result;

            // Remove:
            // data:application/pdf;base64,
            const base64Data = result.split(",")[1];

            resolve(base64Data);
        };

        reader.onerror = function () {
            reject(new Error("Unable to read selected file."));
        };

        reader.readAsDataURL(file);
    });
}


// ----------------------------------------------------------
// Check Submission Status
// ----------------------------------------------------------

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
                <p>${data.error || data.message || "Unknown error"}</p>
            `;
            return;
        }

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