let currentStep = 1;

function showStep(step) {
    for (let i = 1; i <= 6; i++) {
        document.getElementById("step" + i).classList.add("hidden");
    }
    document.getElementById("step" + step).classList.remove("hidden");
}

function nextStep() {
    currentStep++;
    showStep(currentStep);
}

const API = "http://127.0.0.1:5000";

async function submitAll() {

    const fileName = document.getElementById("file").files[0]?.name;

    const payload = {
        team_name: document.getElementById("team_name").value,
        region: document.getElementById("region").value,
        institution: document.getElementById("institution").value,

        leader_name: document.getElementById("leader_name").value,
        leader_email: document.getElementById("leader_email").value,
        leader_phone: document.getElementById("leader_phone").value,

        mission: document.getElementById("mission").value,

        project_title: document.getElementById("project_title").value,
        description: document.getElementById("description").value,
        problem_statement: document.getElementById("problem").value,
        solution: document.getElementById("solution").value,
        impact: document.getElementById("impact").value,
        technologies: document.getElementById("tech").value,
        github: document.getElementById("github").value,

        files: fileName
    };

    const res = await fetch(`${API}/apply`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload)
    });

    const data = await res.json();

    document.getElementById("result").innerText =
        "✅ Submitted! ID: " + data.application_id;
}