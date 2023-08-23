using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using RiaMoneyTransferAPI.Model;
using RiaMoneyTransferAPI.Service;

namespace RiaMoneyTransferAPI.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class UserController : ControllerBase
    {
        private readonly IUserService _userService;
        public UserController(IUserService userService)
        {
            _userService = userService;            
        }

        [HttpGet("/GetAllUsers")]

        public async Task<IActionResult> Get() { 
        
            var users= _userService.GetUsers();
            if (users == null || users.Count == 0)
            {
                return NoContent();
            }
            return Ok(users);
        }

        [HttpPost("/AddUser")]
        public async Task<IActionResult> Post([FromBody] User [] users)
        {
            _userService.AddUsers(users);

            return Ok(_userService.GetUsers());
        }

    }
}
