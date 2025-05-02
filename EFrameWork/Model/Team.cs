using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using System.Linq;
using System.Threading.Tasks;

namespace EFrameWork.Model
{
    public class Team
    {
        [Key]
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public int TeamID { get; set; }
        [Required]
        public string TeamName { get; set; }

        public ICollection<Task> Tasks { get; set; }
        public ICollection<User> Users { get; set; }
    }
}