function closeWindow() {
    if (window.opener && !window.opener.closed) {
        window.close();
    } else {
        alert("Это окно нельзя закрыть автоматически. Пожалуйста, закройте его вручную.");
    }
}