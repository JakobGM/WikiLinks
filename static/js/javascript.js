// Determines the end date of the current semester
function semesterEnd() {
  var nowDate = new Date();
  if (nowDate.getMonth() <=  6) {
    return new Date(nowDate.getFullYear(), 6, 32).toUTCString(); // 31st of July, this year
  }
  else {
    return new Date(nowDate.getFullYear(), 11, 32).toUTCString(); // 31st of December, this year
  }
}

// Redirects to user-specified 1024-calendar
function calendarRedirect() {
  var calendarName = getCookie("calendarName");

  if (calendarName == undefined || calendarName === "") {
    calendarName = window.prompt("Tast inn ditt kalendernavn på ntnu.1024.no. " +
    "Du blir deretter sendt direkte til din kalender neste gang. " +
    "Kalendernavnet kan endres ved å trykke på tannhjulet oppe i venstre hjørne.");

    if (calendarName == undefined) {
      return; // Exits function if user didn´t enter a calendar name
    }
    document.cookie="calendarName=" + calendarName +
    "; expires=" + new Date(new Date().getFullYear() + 5, 11, 32).toUTCString(); // Sets expiry date 5 years into future
    calendarRedirect();
  }
  else {
    window.location = "http://ntnu.1024.no/" + calendarName;
  }
}

function changeCalendarName() {
  var calendarName = getCookie("calendarName");

  if (calendarName == undefined) {
    calendarName = window.prompt("Tast inn ditt kalendernavn på ntnu.1024.no. " +
    "Trykker du på \"1024-kalender\"-linken under \"Annet\"-seksjonen blir du " +
    "så sendt direkte til din kalender.");
  }
  else {
    calendarName = window.prompt("Tast inn ditt kalendernavn på ntnu.1024.no. " +
    "Trykker du på \"1024-kalender\"-linken under \"Annet\"-seksjonen blir du " +
    "så sendt direkte til din kalender.", calendarName);
  }

  if (calendarName == undefined) {
    return; // No change is made if user selects the cancel dialogue box
  }
  else if (calendarName === "") {
    deleteCookie("calendarName"); // Deletes cookie if user enters empty value
  }
  else {
    document.cookie="calendarName=" + calendarName +
    "; expires=" + new Date(new Date().getFullYear() + 5, 11, 32).toUTCString(); // Sets expiry date 5 years into future
    location.reload();
  }
}
