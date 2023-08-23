using Microsoft.AspNetCore.Mvc;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace RiaMoneyTransferAPI.Model
{
    public class User 
    {
        [Required]
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        [Key]
        public int id { get; set; }
        [Required]
        public string lastName { get; set; }
        [Required]
        public string firstName { get; set; }

        [Required]
        [Range(19,90)]
        public int age { get; set; }

        
    }
}
