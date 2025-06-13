function getCSRFToken() {
  const cookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
  return cookie ? cookie.split('=')[1] : '';
}

function addStudent() {
  const csrftoken = getCSRFToken();
  const payload = {
    name: document.getElementById('name').value,
    subject: document.getElementById('subject').value,
    marks: parseInt(document.getElementById('marks').value)
  };

  fetch('/add/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrftoken
    },
    body: JSON.stringify(payload)
  })
  .then(res => res.json())
  .then(data => {
    if (data.status === 'success') {
      location.reload();
    } else {
      alert("Failed to add student: " + data.message);
    }
  })
  .catch(err => {
    alert("Error occurred: " + err);
  });
}



function updateStudent(btn) {
  const row = btn.closest('tr');
  fetch('/update/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken()},
    body: JSON.stringify({
      id: row.dataset.id,
      name: row.children[0].innerText,
      subject: row.children[1].innerText,
      marks: parseInt(row.children[2].innerText),
    })
  }).then(res => res.json()).then(data => alert(data.status));
}

function deleteStudent(btn) {
  const row = btn.closest('tr');
  fetch('/delete/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken()},
    body: JSON.stringify({ id: row.dataset.id })
  }).then(res => res.json()).then(data => {
    if (data.status === 'deleted') row.remove();
  });
}

function showAddModal() {
  document.getElementById('modal').style.display = 'block';
}
