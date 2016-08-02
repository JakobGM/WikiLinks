// Redirects to user-specified 1024-calendar
function calendarRedirect() {
  var calendarName = window.prompt("Tast inn ditt kalendernavn på ntnu.1024.no. " +
                  "Du blir deretter sendt direkte til din kalender neste gang. ");

  if (calendarName == undefined) {
    return; // Exits function if user didn´t enter a calendar name
  }

  window.location = "/kalender/" + calendarName;
}